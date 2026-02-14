import zipfile
import os

class Packager:
    def __init__(self, output_root):
        self.output_root = output_root
        if not os.path.exists(output_root):
            os.makedirs(output_root)

    def generate_filename(self, pattern, context):
        """
        根据模式生成文件名
        pattern 示例: "{TaskName}_{ImageSeq}_{GridIndex}.png"
        context: 包含所有变量的字典
        """
        return pattern.format(**context)

    def pack_results(self, task_name, image_seq, image_list, naming_pattern="{TaskName}_{ImageSeq}_{GridIndex}.png"):
        """
        将一组图片打包成 ZIP 或 保存到文件夹
        :param task_name: 任务名称
        :param image_seq: 图片序列号 (string, e.g., '01')
        :param image_list: 包含 PIL Image 和元数据的列表
        :param naming_pattern: 命名规则
        :return: zip_path
        """
        # 创建临时文件夹 (可选，也可以直接写入 zip)
        temp_dir = os.path.join(self.output_root, f"{task_name}_{image_seq}_Temp")
        os.makedirs(temp_dir, exist_ok=True)
        
        saved_paths = []
        
        # 1. 保存所有单张图片
        for item in image_list:
            img = item['image']
            # 构建上下文变量
            ctx = {
                "TaskName": task_name,
                "ImageSeq": image_seq,
                "GridIndex": item['index'], # 1-9
                "Row": item['row'],
                "Col": item['col'],
                "W": img.width,
                "H": img.height
            }
            
            filename = self.generate_filename(naming_pattern, ctx)
            save_path = os.path.join(temp_dir, filename)
            img.save(save_path, quality=95)
            saved_paths.append(save_path)
            
        # 2. 创建 ZIP ({TaskName}_{ImageSeq}.zip)
        zip_filename = f"{task_name}_{image_seq}.zip"
        zip_path = os.path.join(self.output_root, zip_filename)
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for p in saved_paths:
                zf.write(p, arcname=os.path.basename(p))
                
        # 3. 清理临时文件 (可选)
        for p in saved_paths:
            os.remove(p)
        os.rmdir(temp_dir)
                
        return zip_path
