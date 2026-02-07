import os
from datetime import datetime
from src.utils.logger import logger

class DiaryStorage:
    """
    日记文件存储服务
    """
    def __init__(self, file_path):
        self.file_path = file_path
        self._ensure_dir()

    def _ensure_dir(self):
        if os.path.dirname(self.file_path):
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

    def append(self, content):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        header = f"\n## {timestamp}\n"
        try:
            with open(self.file_path, 'a', encoding='utf-8') as f:
                f.write(header)
                f.write(content + "\n")
            logger.info(f"[Memory] 日记已写入: {self.file_path}")
        except Exception as e:
            logger.error(f"[Memory] 日记写入失败: {e}", exc_info=True)
