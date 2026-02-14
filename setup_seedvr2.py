"""
SeedVR2-GGUF 一键配置脚本
=========================
用途：克隆 SeedVR2 引擎仓库、安装依赖、下载 GGUF 模型文件。

使用方法:
    python setup_seedvr2.py [--model Q4_K_M|Q5_K_M|Q8_0|Q3_K_M|Q6_K]
"""

import os
import sys
import subprocess
import argparse
import shutil

# --- 配置 ---
ENGINE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seedvr2_engine")
MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "SeedVR2")
REPO_URL = "https://github.com/numz/ComfyUI-SeedVR2_VideoUpscaler.git"

# 可用的 GGUF 量化版本 (3B)
GGUF_MODELS = {
    "Q3_K_M": {
        "filename": "seedvr2_ema_3b-Q3_K_M.gguf",
        "url": "https://huggingface.co/cmeka/SeedVR2-GGUF/resolve/main/seedvr2_ema_3b-Q3_K_M.gguf",
        "size": "1.55 GB",
    },
    "Q4_K_M": {
        "filename": "seedvr2_ema_3b-Q4_K_M.gguf",
        "url": "https://huggingface.co/cmeka/SeedVR2-GGUF/resolve/main/seedvr2_ema_3b-Q4_K_M.gguf",
        "size": "2 GB",
    },
    "Q5_K_M": {
        "filename": "seedvr2_ema_3b-Q5_K_M.gguf",
        "url": "https://huggingface.co/cmeka/SeedVR2-GGUF/resolve/main/seedvr2_ema_3b-Q5_K_M.gguf",
        "size": "2.41 GB",
    },
    "Q6_K": {
        "filename": "seedvr2_ema_3b-Q6_K.gguf",
        "url": "https://huggingface.co/cmeka/SeedVR2-GGUF/resolve/main/seedvr2_ema_3b-Q6_K.gguf",
        "size": "2.85 GB",
    },
    "Q8_0": {
        "filename": "seedvr2_ema_3b-Q8_0.gguf",
        "url": "https://huggingface.co/cmeka/SeedVR2-GGUF/resolve/main/seedvr2_ema_3b-Q8_0.gguf",
        "size": "3.66 GB",
    },
    # --- 7B 模型 (画质更好但更慢) ---
    "7B_Q4_K_M": {
        "filename": "seedvr2_ema_7b-Q4_K_M.gguf",
        "url": "https://huggingface.co/cmeka/SeedVR2-GGUF/resolve/main/seedvr2_ema_7b-Q4_K_M.gguf",
        "size": "4.5 GB",
    },
    "7B_Q8_0": {
        "filename": "seedvr2_ema_7b-Q8_0.gguf",
        "url": "https://huggingface.co/cmeka/SeedVR2-GGUF/resolve/main/seedvr2_ema_7b-Q8_0.gguf",
        "size": "7.7 GB",
    },
}

# VAE 模型 (SeedVR2 需要配套的 VAE)
VAE_URL = "https://huggingface.co/numz/SeedVR2_comfyUI/resolve/main/seedvr2_vae.safetensors"
VAE_FILENAME = "seedvr2_vae.safetensors"


def download_file(url, save_path, description=""):
    """使用 requests 或 curl 下载大文件（带进度条）"""
    # 尝试使用 curl（更可靠地处理大文件）
    if shutil.which("curl"):
        print(f"📥 正在下载 {description}...")
        print(f"   URL: {url}")
        print(f"   保存到: {save_path}")
        result = subprocess.run(
            ["curl", "-L", "-o", save_path, "--progress-bar", url],
            check=False
        )
        if result.returncode == 0 and os.path.exists(save_path):
            size_mb = os.path.getsize(save_path) / 1024 / 1024
            print(f"   [OK] 下载完成 ({size_mb:.1f} MB)")
            return True
        else:
            print(f"   [ERR] curl 下载失败")
            return False

    # 回退到 requests
    try:
        import requests
        print(f"📥 正在下载 {description}...")
        print(f"   URL: {url}")
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        total = int(response.headers.get('content-length', 0))
        downloaded = 0
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192 * 16):
                f.write(chunk)
                downloaded += len(chunk)
                if total > 0:
                    pct = downloaded / total * 100
                    print(f"\r   进度: {pct:.1f}% ({downloaded/1024/1024:.1f}/{total/1024/1024:.1f} MB)", end="")
        print(f"\n   [OK] 下载完成")
        return True
    except Exception as e:
        print(f"   [ERR] 下载失败: {e}")
        return False


def step_clone_repo():
    """Step 1: 克隆 SeedVR2 仓库"""
    print("\n" + "=" * 60)
    print("[STEP 1/4] 克隆 SeedVR2 引擎仓库")
    print("=" * 60)

    if os.path.exists(os.path.join(ENGINE_DIR, "inference_cli.py")):
        print(f"   [INFO] 引擎目录已存在: {ENGINE_DIR}")
        print("   跳过克隆。如需重新克隆，请先删除该目录。")
        return True

    os.makedirs(os.path.dirname(ENGINE_DIR), exist_ok=True)
    print(f"   正在克隆 {REPO_URL}...")
    result = subprocess.run(
        ["git", "clone", "--depth", "1", REPO_URL, ENGINE_DIR],
        check=False,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"   [ERR] 克隆失败: {result.stderr}")
        return False

    print(f"   [OK] 克隆成功: {ENGINE_DIR}")
    return True


def step_install_deps():
    """Step 2: 安装 SeedVR2 依赖"""
    print("\n" + "=" * 60)
    print("[STEP 2/4] 安装 SeedVR2 Python 依赖")
    print("=" * 60)

    req_file = os.path.join(ENGINE_DIR, "requirements.txt")
    if not os.path.exists(req_file):
        print(f"   [ERR] 未找到 requirements.txt: {req_file}")
        return False

    print(f"   正在安装依赖 (来自 {req_file})...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", req_file],
        check=False,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"   [WARN] 部分依赖安装可能失败:")
        # 只显示最后几行错误
        lines = result.stderr.strip().split('\n')
        for line in lines[-10:]:
            print(f"      {line}")
        print("   请手动检查并安装缺失的依赖。")
        return True  # 不阻断流程

    print("   [OK] 依赖安装完成")
    return True


def step_download_model(model_key="Q4_K_M"):
    """Step 3: 下载 GGUF 模型"""
    print("\n" + "=" * 60)
    print(f"[STEP 3/4] 下载 SeedVR2 GGUF 模型 ({model_key})")
    print("=" * 60)

    if model_key not in GGUF_MODELS:
        print(f"   [ERR] 未知的模型版本: {model_key}")
        print(f"   可选版本: {', '.join(GGUF_MODELS.keys())}")
        return False

    model_info = GGUF_MODELS[model_key]
    os.makedirs(MODELS_DIR, exist_ok=True)
    save_path = os.path.join(MODELS_DIR, model_info["filename"])

    if os.path.exists(save_path):
        size_mb = os.path.getsize(save_path) / 1024 / 1024
        print(f"   [INFO] 模型文件已存在: {save_path} ({size_mb:.1f} MB)")
        print("   跳过下载。")
        return True

    print(f"   模型: {model_info['filename']} (预计大小: {model_info['size']})")
    return download_file(model_info["url"], save_path, f"DiT 模型 ({model_key})")


def step_download_vae():
    """Step 4: 下载 VAE 模型"""
    print("\n" + "=" * 60)
    print("[STEP 4/4] 下载 SeedVR2 VAE 模型")
    print("=" * 60)

    os.makedirs(MODELS_DIR, exist_ok=True)
    save_path = os.path.join(MODELS_DIR, VAE_FILENAME)

    if os.path.exists(save_path):
        size_mb = os.path.getsize(save_path) / 1024 / 1024
        print(f"   [INFO] VAE 模型已存在: {save_path} ({size_mb:.1f} MB)")
        print("   跳过下载。")
        return True

    return download_file(VAE_URL, save_path, "VAE 模型")


def verify_installation():
    """验证安装是否完成"""
    print("\n" + "=" * 60)
    print("🔍 验证安装")
    print("=" * 60)

    checks = {
        "SeedVR2 引擎": os.path.exists(os.path.join(ENGINE_DIR, "inference_cli.py")),
        "DiT 模型": any(
            os.path.exists(os.path.join(MODELS_DIR, m["filename"]))
            for m in GGUF_MODELS.values()
        ),
        "VAE 模型": os.path.exists(os.path.join(MODELS_DIR, VAE_FILENAME)),
    }

    all_ok = True
    for name, ok in checks.items():
        status = "[OK]" if ok else "[X]"
        print(f"   {status} {name}")
        if not ok:
            all_ok = False

    if all_ok:
        print("\n[OK] SeedVR2 配置完成！你现在可以在 Web 界面中选择 SeedVR2 引擎了。")
    else:
        print("\n[WARN] 部分组件缺失，请检查上方的错误信息。")

    return all_ok


def main():
    parser = argparse.ArgumentParser(description="SeedVR2-GGUF 一键配置脚本")
    parser.add_argument(
        "--model",
        choices=list(GGUF_MODELS.keys()),
        default="Q4_K_M",
        help="选择 GGUF 量化版本 (默认: Q4_K_M, 约 2GB)"
    )
    parser.add_argument(
        "--skip-deps",
        action="store_true",
        help="跳过依赖安装步骤"
    )
    args = parser.parse_args()

    print("SeedVR2-GGUF 配置向导")
    print("=" * 60)
    print(f"   引擎目录: {ENGINE_DIR}")
    print(f"   模型目录: {MODELS_DIR}")
    print(f"   GGUF 版本: {args.model} ({GGUF_MODELS[args.model]['size']})")
    print("=" * 60)

    # Step 1: 克隆仓库
    if not step_clone_repo():
        print("\n[ERR] 配置失败：无法克隆 SeedVR2 仓库。")
        sys.exit(1)

    # Step 2: 安装依赖
    if not args.skip_deps:
        step_install_deps()

    # Step 3: 下载 GGUF 模型
    if not step_download_model(args.model):
        print("\n[WARN] 模型下载失败。你可以稍后手动下载。")

    # Step 4: 下载 VAE
    if not step_download_vae():
        print("\n[WARN] VAE 下载失败。你可以稍后手动下载。")

    # 验证
    verify_installation()


if __name__ == "__main__":
    main()
