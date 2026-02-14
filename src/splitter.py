from PIL import Image
import os

class GridSplitter:
    def __init__(self, output_dir):
        self.output_dir = output_dir

    def split_3x3(self, image_path, task_id):
        """
        加载图片并切割为 3x3 网格
        返回: 切割后的 Image 对象列表
        :param image_path: 原图路径
        :param task_id: 任务ID (用于日志或其他用途)
        :return: tiles (list of dict)
        """
        try:
            img = Image.open(image_path).convert('RGB')
        except Exception as e:
            print(f"Error opening image {image_path}: {e}")
            return []
            
        width, height = img.size
        
        # 计算每个格子的宽高 (均匀分布)
        tile_w = width // 3
        tile_h = height // 3
        
        tiles = []
        for i in range(3):      # Row (0, 1, 2)
            for j in range(3):  # Col (0, 1, 2)
                left = j * tile_w
                upper = i * tile_h
                right = left + tile_w
                lower = upper + tile_h
                
                # 裁剪
                tile = img.crop((left, upper, right, lower))
                tiles.append({
                    "image": tile,
                    "index": i * 3 + j + 1, # 1-9
                    "row": i + 1,
                    "col": j + 1
                })
        return tiles
