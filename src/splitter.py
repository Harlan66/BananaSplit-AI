from PIL import Image
import os

class GridSplitter:
    def __init__(self, output_dir):
        self.output_dir = output_dir

    def split_grid(self, image_path, task_id, rows=3, cols=3):
        """
        加载图片并切割为 rows x cols 网格
        返回: 切割后的 Image 对象列表
        :param image_path: 原图路径
        :param task_id: 任务ID
        :param rows: 行数
        :param cols: 列数
        :return: tiles (list of dict)
        """
        try:
            img = Image.open(image_path).convert('RGB')
        except Exception as e:
            print(f"Error opening image {image_path}: {e}")
            return []
            
        width, height = img.size
        
        # 计算每个格子的宽高 (均匀分布)
        tile_w = width // cols
        tile_h = height // rows
        
        tiles = []
        for i in range(rows):      # Row
            for j in range(cols):  # Col
                left = j * tile_w
                upper = i * tile_h
                right = left + tile_w
                lower = upper + tile_h
                
                # 裁剪
                tile = img.crop((left, upper, right, lower))
                tiles.append({
                    "image": tile,
                    "index": i * cols + j + 1,
                    "row": i + 1,
                    "col": j + 1
                })
        return tiles

    def split_3x3(self, image_path, task_id):
        return self.split_grid(image_path, task_id, rows=3, cols=3)
