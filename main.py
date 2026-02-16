import os
import sys
import argparse
from tqdm import tqdm
from src.splitter import GridSplitter
from src.upscaler import AIUpscaler
from src.packager import Packager

# --- 配置区 ---
INPUT_DIR = "./inputs"
OUTPUT_DIR = "./outputs"
MODELS_DIR = "./models"
NAMING_PATTERN = "{TaskName}_{ImageSeq}_{GridIndex}.png" # 自定义命名规则
# ----------------

def ensure_dirs():
    """确保所有必要的目录存在"""
    os.makedirs(INPUT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(MODELS_DIR, exist_ok=True)
    # 创建一个__init__.py在src下如果已存在src
    if not os.path.exists("src/__init__.py"):
        with open("src/__init__.py", "w") as f:
            pass

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="九宫格图像处理工具")
    parser.add_argument(
        "--engine", choices=["realesrgan", "seedvr2"], default="realesrgan",
        help="AI 放大引擎 (默认: realesrgan)"
    )
    parser.add_argument(
        "--model", default=None,
        help="GGUF 模型文件名 (仅 SeedVR2, 默认: seedvr2_ema_3b-Q4_K_M.gguf)"
    )
    parser.add_argument(
        "--rows", type=int, default=3,
        help="Grid rows (default: 3)"
    )
    parser.add_argument(
        "--cols", type=int, default=3,
        help="Grid columns (default: 3)"
    )
    args = parser.parse_args()

    print("🚀 初始化九宫格图像处理工作流...")
    print(f"   AI 引擎: {args.engine}")
    
    # 0. 检查目录
    ensure_dirs()
    
    # 1. 获取任务名称
    task_name = input("请输入任务名称 (TaskName): ").strip()
    if not task_name:
        task_name = "DefaultTask"
        print(f"⚠️ 未输入名称，使用默认: {task_name}")
        
    # 2. 初始化核心模块
    print("📦 加载模块中...")
    splitter = GridSplitter(OUTPUT_DIR)
    
    print("⚡ 加载 AI 模型 (首次运行需下载权重)...")
    if args.engine == "seedvr2":
        from src.upscaler_seed import SeedUpscaler
        model_name = args.model or "seedvr2_ema_3b-Q4_K_M.gguf"
        upscaler = SeedUpscaler(model_name=model_name)
        if not upscaler.is_ready:
            print("❌ SeedVR2 未就绪。请先运行 python setup_seedvr2.py")
            return
    else:
        model_path = os.path.join(MODELS_DIR, "RealESRGAN_x4plus.pth")
        upscaler = AIUpscaler(model_path=model_path)
    
    packager = Packager(OUTPUT_DIR)
    
    # 3. 获取输入文件列表
    input_files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
    input_files.sort() # 确保处理顺序一致
    
    if not input_files:
        print(f"❌ '{INPUT_DIR}' 目录下未找到图片文件！请放入图片后重试。")
        return

    print(f"🔍 发现 {len(input_files)} 个待处理文件。开始批处理...")
    
    # 4. 主循环
    for idx, filename in enumerate(input_files):
        current_seq = f"{idx+1:02d}" # 01, 02...
        file_path = os.path.join(INPUT_DIR, filename)
        
        print(f"\n[{current_seq}/{len(input_files)}] 正在处理: {filename} ...")
        
        # Step 1: 裁切
        print(f"   ✂️ 正在切分 {args.rows}x{args.cols} 网格...")
        tiles = splitter.split_grid(file_path, task_name, rows=args.rows, cols=args.cols)
        if not tiles:
            print(f"   ❌ 切分失败，跳过此文件。")
            continue
        
        # Step 2: 增强 (批处理)
        # 使用 tqdm 显示进度条
        enhanced_tiles = []
        for tile_data in tqdm(tiles, desc="   ✨ AI 增强中", unit="slice"):
            enhanced_img = upscaler.enhance(tile_data['image'])
            
            # 更新数据
            tile_data['image'] = enhanced_img
            enhanced_tiles.append(tile_data)
            
        # Step 3: 打包
        print(f"   📦 正在打包...")
        try:
            zip_path = packager.pack_results(
                task_name=task_name,
                image_seq=current_seq,
                image_list=enhanced_tiles, 
                naming_pattern=NAMING_PATTERN
            )
            print(f"   ✅ 完成! 输出: {zip_path}")
        except Exception as e:
            print(f"   ❌ 打包失败: {e}")

    print("\n✅ 所有任务已完成！请检查 outputs 文件夹。")

if __name__ == "__main__":
    # 为了避免 ImportError，我们需要确保当前目录在 sys.path 中
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    main()
