import streamlit as st
import os
import time
from PIL import Image
from src.splitter import GridSplitter
from src.upscaler import AIUpscaler
from src.packager import Packager
from src.upscaler_seed import SeedUpscaler, check_seedvr2_available, get_available_models
import zipfile

# --- 配置 ---
st.set_page_config(
    page_title="九宫格 AI 增强助手",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 样式美化
st.markdown("""
<style>
    .reportview-container {
        background: #f0f2f6;
    }
    .main-header {
        font-family: 'Helvetica Neue', sans-serif;
        color: #333;
        text-align: center;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #ff4b4b; 
        color: white;
    }
    .stSuccess {
        background-color: #d4edda;
        color: #155724;
        padding: 10px;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# 状态初始化
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'results' not in st.session_state:
    st.session_state.results = []

def main():
    st.title("✨ 九宫格图像智能切分与增强")
    st.markdown("---")

    # [Sidebar] 配置区
    with st.sidebar:
        st.header("⚙️ 任务设置")
        task_name = st.text_input("任务名称 (Task Name)", value="MyProject", help="用于生成文件名的前缀")
        
        st.subheader("切分设置 (Grid)")
        col_r, col_c = st.columns(2)
        with col_r:
            rows = st.number_input("行数 (Rows)", min_value=1, value=3, step=1)
        with col_c:
            cols = st.number_input("列数 (Cols)", min_value=1, value=3, step=1)
        
        st.subheader("输出设置")
        res_mode = st.selectbox(
            "目标分辨率 (单图长边)", 
            ["社交媒体 (1080p)", "高清 (2K)", "超清 (4K)", "原比例 (AI 默认 x4)"],
            index=3
        )
        
        # 映射分辨率
        res_map = {
            "社交媒体 (1080p)": 1080,
            "高清 (2K)": 2048,
            "超清 (4K)": 3840,
            "原比例 (AI 默认 x4)": None
        }
        target_res = res_map[res_mode]
        
        st.info("💡 提示：降低分辨率可以显著减小文件体积。")
        
        # --- AI 引擎选择 ---
        st.markdown("---")
        st.subheader("🤖 AI 引擎")
        
        seedvr2_available = check_seedvr2_available()
        
        engine_options = ["Real-ESRGAN (快速/默认)"]
        if seedvr2_available:
            engine_options.append("SeedVR2-GGUF (画质增强)")
        else:
            engine_options.append("SeedVR2-GGUF (未配置)")
        
        engine_choice = st.selectbox(
            "选择 AI 放大引擎",
            engine_options,
            index=0,
            help="Real-ESRGAN 速度快、兼容性好；SeedVR2 画质更精细但速度较慢"
        )
        
        use_seedvr2 = "SeedVR2" in engine_choice
        
        # SeedVR2 设置面板
        seedvr2_config = {}
        if use_seedvr2:
            if not seedvr2_available:
                st.warning("⚠️ SeedVR2 尚未配置。请在终端运行：\n```\npython setup_seedvr2.py\n```")
            else:
                with st.expander("🔧 SeedVR2 高级设置", expanded=False):
                    # 模型选择
                    available_models = get_available_models()
                    if available_models:
                        model_labels = [f"{q} ({fn})" for q, fn in available_models]
                        selected_idx = st.selectbox(
                            "GGUF 量化版本",
                            range(len(model_labels)),
                            format_func=lambda i: model_labels[i],
                            index=0,
                            help="Q4_K_M 平衡画质与速度；7B_Q4_K_M 画质最好 (推荐 3060 12G+)"
                        )
                        seedvr2_config["model_name"] = available_models[selected_idx][1]
                    
                    # 画质参数
                    st.caption("AI 画质参数")
                    seedvr2_config["input_noise_scale"] = st.slider(
                        "AI 幻想程度 (Input Noise)", 
                        0.0, 1.0, 0.2, 0.1,
                        help="0.0=保守修复 (类似 ESRGAN); 0.2-0.3=增强纹理细节; >0.5=显著重绘 (可能会变样)"
                    )

                    # 显存优化
                    st.caption("显存优化选项")
                    seedvr2_config["cpu_offload"] = st.checkbox(
                        "CPU 卸载 (推荐 ≤12GB 显存)", value=True
                    )
                    seedvr2_config["vae_tiling"] = st.checkbox(
                        "VAE Tiling (推荐 ≤8GB 显存)", value=True
                    )
                    seedvr2_config["blocks_to_swap"] = st.slider(
                        "BlockSwap 等级 (越高越省显存)",
                        min_value=0, max_value=32, value=16, step=4,
                        help="0=不启用, 32=最大程度省显存 (但较慢)"
                    )
        
    # [Main] 文件上传
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("📂 上传图片")
        uploaded_files = st.file_uploader(
            "拖拽或选择九宫格原图", 
            type=['png', 'jpg', 'jpeg'], 
            accept_multiple_files=True
        )
        
        if uploaded_files:
            st.success(f"已加载 {len(uploaded_files)} 张图片")
            
    with col2:
        st.subheader("🖼️ 预览与处理")
        if not uploaded_files:
            st.info("👈 请先在左侧上传图片")
        else:
            # 预览第一张图
            preview_img = Image.open(uploaded_files[0])
            st.image(preview_img, caption=f"预览: {uploaded_files[0].name}", width=300)
            
            engine_label = "SeedVR2" if use_seedvr2 else "Real-ESRGAN"
            if st.button(f"🚀 开始 AI 处理 ({engine_label} / {res_mode})", key="process_btn"):
                process_images(
                    uploaded_files, task_name, target_res,
                    use_seedvr2=use_seedvr2 and seedvr2_available,
                    seedvr2_config=seedvr2_config,
                    rows=rows,
                    cols=cols
                )

    # [Results] 结果展示区
    st.markdown("---")
    st.subheader("📦 处理结果")
    
    if st.session_state.results:
        for res in st.session_state.results:
            with st.expander(f"✅ {res['filename']} (点击下载)", expanded=True):
                c1, c2 = st.columns([1, 4])
                with c1:
                    st.image(res['preview'], width=100)
                with c2:
                    st.write(f"**任务ID**: {res['task_id']}")
                    st.write(f"**包含文件**: {rows*cols}张高清图 ({rows}x{cols})")
                    
                    with open(res['zip_path'], "rb") as fp:
                        btn = st.download_button(
                            label=f"💾 下载 ZIP 包 ({os.path.getsize(res['zip_path'])/1024/1024:.2f} MB)",
                            data=fp,
                            file_name=os.path.basename(res['zip_path']),
                            mime="application/zip"
                        )

def process_images(files, task_name, target_res=None, use_seedvr2=False, seedvr2_config=None, rows=3, cols=3):
    st.session_state.results = []
    
    # 初始化进度条
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # 路径准备
    output_root = "./outputs"
    os.makedirs(output_root, exist_ok=True)
    os.makedirs("./models", exist_ok=True)
    
    # 加载模型 - 根据引擎选择
    if use_seedvr2:
        status_text.text("⚡ 正在加载 AI 模型 (SeedVR2-GGUF)...")
        try:
            config = seedvr2_config or {}
            upscaler = SeedUpscaler(
                model_name=config.get("model_name", "seedvr2_ema_3b-Q4_K_M.gguf"),
                blocks_to_swap=config.get("blocks_to_swap", 16),
                vae_tiling=config.get("vae_tiling", True),
                cpu_offload=config.get("cpu_offload", True),
                input_noise_scale=config.get("input_noise_scale", 0.2), # 传递噪声参数
            )
            if not upscaler.is_ready:
                st.error("SeedVR2 未就绪。请运行 python setup_seedvr2.py 完成配置。")
                return
        except Exception as e:
            st.error(f"SeedVR2 模型加载失败: {e}")
            return
    else:
        status_text.text("⚡ 正在加载 AI 模型 (Real-ESRGAN)...")
        try:
            upscaler = AIUpscaler(model_path="./models/RealESRGAN_x4plus.pth")
        except Exception as e:
            st.error(f"模型加载失败: {e}")
            return

    splitter = GridSplitter(output_root)
    packager = Packager(output_root)
    
    total_files = len(files)
    
    for idx, uploaded_file in enumerate(files):
        # 1. 保存临时文件 (因为 splitter 需要路径或对象，这里我们稍微修改 splitter 适应流对象，或者存临时)
        # 更加稳健的做法是保存到 inputs
        input_path = os.path.join("./inputs", uploaded_file.name)
        os.makedirs("./inputs", exist_ok=True)
        with open(input_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
            
        current_seq = f"{idx+1:02d}"
        status_text.text(f"正在处理 [{idx+1}/{total_files}]: {uploaded_file.name} - 切分中...")
        
        # 2. 切分
        tiles = splitter.split_grid(input_path, task_name, rows=rows, cols=cols)
        
        # 3. 增强
        enhanced_tiles = []
        total_tiles = len(tiles)
        for t_idx, tile in enumerate(tiles):
            status_text.text(f"正在处理 [{idx+1}/{total_files}]: {uploaded_file.name} - AI 增强切片 {t_idx+1}/{total_tiles}...")
            enh_img = upscaler.enhance(tile['image'], target_long_side=target_res)
            tile['image'] = enh_img
            enhanced_tiles.append(tile)
            
            # 更新子进度
            current_progress = (idx / total_files) + ((t_idx + 1) / total_tiles / total_files)
            progress_bar.progress(min(current_progress, 1.0))

        # 4. 打包
        status_text.text(f"正在处理 [{idx+1}/{total_files}]: 打包 ZIP...")
        zip_path = packager.pack_results(
            task_name=task_name,
            image_seq=current_seq,
            image_list=enhanced_tiles
        )
        
        # 5. 记录结果
        st.session_state.results.append({
            "filename": uploaded_file.name,
            "task_id": f"{task_name}_{current_seq}",
            "zip_path": zip_path,
            "preview": enhanced_tiles[len(enhanced_tiles)//2]['image'] # 预览中间那张
        })
        
    status_text.success("🎉 所有图片处理完成！请在下方下载。")
    progress_bar.progress(100)

if __name__ == "__main__":
    main()
