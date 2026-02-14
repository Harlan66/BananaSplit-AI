"""
SeedVR2-GGUF 图片放大器封装
===========================
通过调用 SeedVR2 官方 inference_cli.py 实现图片超分辨率放大。
接口与 AIUpscaler (Real-ESRGAN) 保持一致。
"""

import os
import sys
import subprocess
import tempfile
import uuid
import shutil
import torch
from PIL import Image

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class SeedUpscaler:
    """SeedVR2-GGUF 图片放大器

    通过 subprocess 调用 SeedVR2 的 inference_cli.py 完成推理。
    接口与 AIUpscaler 保持一致，均通过 enhance(pil_image, ...) 返回增强后的 PIL Image。
    """

    # 默认配置
    DEFAULT_ENGINE_DIR = os.path.join(PROJECT_ROOT, "seedvr2_engine")
    DEFAULT_MODELS_DIR = os.path.join(PROJECT_ROOT, "models", "SeedVR2")

    def __init__(
        self,
        engine_dir=None,
        models_dir=None,
        model_name="seedvr2_ema_3b-Q4_K_M.gguf",
        device=None,
        blocks_to_swap=16,
        vae_tiling=True,
        cpu_offload=True,
        input_noise_scale=0.0,
    ):
        """
        初始化 SeedVR2 放大器。

        :param engine_dir: SeedVR2 引擎目录 (包含 inference_cli.py)
        :param models_dir: GGUF 模型文件目录
        :param model_name: GGUF 模型文件名
        :param device: 推理设备 (默认自动检测)
        :param blocks_to_swap: BlockSwap 数量 (0-32, 越高越省显存但越慢)
        :param vae_tiling: 是否启用 VAE Tiling (省显存)
        :param cpu_offload: 是否启用 CPU 卸载 (省显存)
        :param input_noise_scale: 输入噪声比例 (0.0-1.0，推荐 0.2 增强细节)
        """
        self.engine_dir = engine_dir or self.DEFAULT_ENGINE_DIR
        self.models_dir = models_dir or self.DEFAULT_MODELS_DIR
        self.model_name = model_name
        self.blocks_to_swap = blocks_to_swap
        self.vae_tiling = vae_tiling
        self.cpu_offload = cpu_offload
        self.input_noise_scale = input_noise_scale

        # 设备检测
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        # 验证引擎是否存在
        self.cli_path = os.path.join(self.engine_dir, "inference_cli.py")
        self.model_path = os.path.join(self.models_dir, self.model_name)

        self._ready = False
        self._check_ready()

    def _check_ready(self):
        """检查 SeedVR2 引擎是否已正确配置"""
        errors = []

        if not os.path.exists(self.cli_path):
            errors.append(f"引擎未找到: {self.cli_path}")

        if not os.path.exists(self.model_path):
            errors.append(f"模型未找到: {self.model_path}")

        vae_path = os.path.join(self.models_dir, "seedvr2_vae.safetensors")
        if not os.path.exists(vae_path):
            errors.append(f"VAE 模型未找到: {vae_path}")

        if errors:
            print("[WARN] SeedVR2 未就绪:")
            for e in errors:
                print(f"   - {e}")
            print("   请运行 python setup_seedvr2.py 完成配置。")
            self._ready = False
        else:
            print(f"[OK] SeedVR2 就绪: {self.model_name}")
            self._ready = True

    @property
    def is_ready(self):
        """SeedVR2 是否已正确配置并可用"""
        return self._ready

    def _build_command(self, input_path, output_path, target_resolution=None):
        """构建 inference_cli.py 的命令行参数"""
        cmd = [
            sys.executable,
            self.cli_path,
            input_path,
            "--output", output_path,
            "--output_format", "png",
            "--dit_model", self.model_name,
            "--model_dir", self.models_dir,
            "--batch_size", "1",
        ]

        # 分辨率控制
        if target_resolution:
            cmd.extend(["--resolution", str(target_resolution)])
            cmd.extend(["--max_resolution", str(target_resolution)])

        # 显存优化选项
        if self.cpu_offload:
            cmd.extend(["--dit_offload_device", "cpu"])
            cmd.extend(["--vae_offload_device", "cpu"])

        if self.blocks_to_swap > 0 and self.cpu_offload:
            cmd.extend(["--blocks_to_swap", str(self.blocks_to_swap)])
            cmd.extend(["--swap_io_components"])

        if self.vae_tiling:
            cmd.extend(["--vae_encode_tiled"])
            cmd.extend(["--vae_decode_tiled"])

        # 色彩校正
        cmd.extend(["--color_correction", "lab"])
        
        # 输入噪声 (画质增强关键)
        if self.input_noise_scale > 0:
            cmd.extend(["--input_noise_scale", str(self.input_noise_scale)])

        return cmd

    def enhance(self, pil_image, target_long_side=None):
        """
        输入 PIL Image，输出增强后的 PIL Image。
        接口与 AIUpscaler.enhance() 保持一致。

        :param pil_image: 输入图片 (PIL Image)
        :param target_long_side: 目标长边像素 (如 1080, 2048, 3840)，None 则使用默认
        :return: 增强后的 PIL Image
        """
        if not self._ready:
            print("[ERROR] SeedVR2 未就绪，返回原图。请先运行 python setup_seedvr2.py")
            return pil_image

        # 计算目标分辨率 (SeedVR2 使用短边分辨率)
        w, h = pil_image.size
        if target_long_side:
            # SeedVR2 的 --resolution 是短边，我们需要转换
            if w > h:
                # 横图: 长边=w, 短边=h
                scale = target_long_side / w
                target_short = int(h * scale)
            else:
                # 竖图: 长边=h, 短边=w
                scale = target_long_side / h
                target_short = int(w * scale)
            target_resolution = target_short
        else:
            # 默认：短边提升到原来的 2 倍或至少 1080
            short_side = min(w, h)
            target_resolution = max(short_side * 2, 1080)

        # 创建临时工作目录
        work_dir = tempfile.mkdtemp(prefix="seedvr2_")
        try:
            # 保存输入图片
            input_filename = f"input_{uuid.uuid4().hex[:8]}.png"
            input_path = os.path.join(work_dir, input_filename)
            pil_image.save(input_path, format="PNG")

            # 输出路径
            output_dir = os.path.join(work_dir, "output")
            os.makedirs(output_dir, exist_ok=True)

            # 构建并执行命令
            cmd = self._build_command(input_path, output_dir, target_resolution)
            print(f"[INFO] SeedVR2 推理中... (目标短边: {target_resolution}px)")

            # 强制子进程使用 UTF-8 编码，避免 SeedVR2 引擎内部的 Emoji
            # 在 Windows GBK 控制台下触发 UnicodeEncodeError
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10 分钟超时
                cwd=self.engine_dir,
                env=env,
                encoding="utf-8",
                errors="replace",
            )

            if result.returncode != 0:
                print(f"[ERROR] SeedVR2 推理失败:")
                # 显示最后几行错误
                stderr_lines = result.stderr.strip().split('\n')
                for line in stderr_lines[-5:]:
                    print(f"   {line}")
                return pil_image

            # 查找输出文件
            output_files = []
            for root, dirs, files in os.walk(output_dir):
                for f in files:
                    if f.lower().endswith(('.png', '.jpg', '.jpeg')):
                        output_files.append(os.path.join(root, f))

            # 如果 output_dir 里没有，检查 work_dir
            if not output_files:
                for f in os.listdir(work_dir):
                    if f.lower().endswith(('.png', '.jpg', '.jpeg')) and f != input_filename:
                        output_files.append(os.path.join(work_dir, f))

            if not output_files:
                print("[ERROR] 未找到 SeedVR2 输出文件")
                print(f"   stdout: {result.stdout[-200:]}")
                return pil_image

            # 读取输出图片
            output_image = Image.open(output_files[0]).convert("RGB")

            # 如果设置了 target_long_side，确保输出尺寸匹配
            if target_long_side:
                out_w, out_h = output_image.size
                current_long = max(out_w, out_h)
                if abs(current_long - target_long_side) > 10:
                    # 需要进一步缩放到精确尺寸
                    if out_w > out_h:
                        new_w = target_long_side
                        new_h = int(out_h * target_long_side / out_w)
                    else:
                        new_h = target_long_side
                        new_w = int(out_w * target_long_side / out_h)
                    output_image = output_image.resize(
                        (new_w, new_h), Image.LANCZOS
                    )

            print(f"[OK] SeedVR2 增强完成: {output_image.size[0]}x{output_image.size[1]}")
            return output_image

        except subprocess.TimeoutExpired:
            print("[ERROR] SeedVR2 推理超时 (10分钟)")
            return pil_image
        except Exception as e:
            print(f"[ERROR] SeedVR2 推理异常: {e}")
            return pil_image
        finally:
            # 清理临时文件
            try:
                shutil.rmtree(work_dir, ignore_errors=True)
            except Exception:
                pass


def check_seedvr2_available():
    """检查 SeedVR2 是否可用（不加载模型）"""
    engine_dir = SeedUpscaler.DEFAULT_ENGINE_DIR
    models_dir = SeedUpscaler.DEFAULT_MODELS_DIR

    cli_exists = os.path.exists(os.path.join(engine_dir, "inference_cli.py"))
    model_exists = any(
        os.path.exists(os.path.join(models_dir, f"seedvr2_ema_3b-{q}.gguf"))
        for q in ["Q3_K_M", "Q4_K_M", "Q5_K_M", "Q6_K", "Q8_0"]
    )
    vae_exists = os.path.exists(os.path.join(models_dir, "seedvr2_vae.safetensors"))

    return cli_exists and model_exists and vae_exists


def get_available_models():
    """获取已下载的 SeedVR2 模型列表"""
    models_dir = SeedUpscaler.DEFAULT_MODELS_DIR
    available = []
    
    # 3B Models
    for q in ["Q3_K_M", "Q4_K_M", "Q5_K_M", "Q6_K", "Q8_0"]:
        filename = f"seedvr2_ema_3b-{q}.gguf"
        if os.path.exists(os.path.join(models_dir, filename)):
            available.append((f"3B_{q}", filename))
            
    # 7B Models (New)
    for q in ["Q4_K_M", "Q8_0"]:
        filename = f"seedvr2_ema_7b-{q}.gguf"
        if os.path.exists(os.path.join(models_dir, filename)):
            available.append((f"7B_{q}", filename))
            
    return available
