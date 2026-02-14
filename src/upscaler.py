from .rrdbnet_arch import RRDBNet
from .realesrgan_model import RealESRGANer
import numpy as np
import os
import torch
from PIL import Image

class AIUpscaler:
    def __init__(self, model_path='models/RealESRGAN_x4plus.pth', device=None):
        # 0. Device selection
        if device is None:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = torch.device(device)
        
        print(f"DEVICE: {self.device}")
        
        # 1. 初始化模型架构 (RealESRGAN_x4plus)
        model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
        
        # 2. 检查模型路径，如果不存在则尝试自动下载
        if not os.path.exists(model_path):
            print(f"⚠️ Model weights not found at {model_path}. Downloading...")
            self.download_model(model_path)
            
        # 3. 加载增强器 (Moved outside of download_model)
        try:
            self.upscaler = RealESRGANer(
                scale=4,
                model_path=model_path,
                model=model,
                tile=400,  # 显存不够时可设为 400
                tile_pad=10,
                pre_pad=0,
                half=True if self.device.type == 'cuda' else False,
                device=self.device
            )
            print("✅ RealESRGANer loaded successfully.")
        except Exception as e:
            print(f"❌ Error initializing RealESRGANer: {e}")
            self.upscaler = None

    def download_model(self, save_path):
        import requests
        url = 'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth'
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"✅ Model downloaded successfully to {save_path}")
        except Exception as e:
            print(f"❌ Failed to download model: {e}\nPlease download manually from {url}")

    def enhance(self, pil_image, target_long_side=None):
        """
        输入 PIL Image，输出增强后的 PIL Image
        :param pil_image: 输入图片
        :param target_long_side: 目标长边像素 (如 1080, 1440, 2160)，None 则使用 AI 默认 x4
        :return: 增强后的图片
        """
        if self.upscaler is None:
            return pil_image # 降级返回原图

        # PIL -> CV2 (Numpy)
        img_np = np.array(pil_image)
        h_input, w_input = img_np.shape[:2]
        
        # 计算 outscale
        outscale = 4.0 # 默认 x4
        if target_long_side:
            current_long_side = max(h_input, w_input)
            outscale = target_long_side / current_long_side

        try:
            # Real-ESRGAN 推理
            output, _ = self.upscaler.enhance(img_np, outscale=outscale)
        except Exception as e:
            print(f"Error during enhancement: {e}")
            return pil_image
            
        # CV2 -> PIL
        return Image.fromarray(output)
