import json
import os

class JsonStorage:
    """
    JSON 文件存储服务 (长期记忆)
    """
    def __init__(self, file_path):
        self.file_path = file_path
        self._ensure_dir()

    def _ensure_dir(self):
        if os.path.dirname(self.file_path):
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

    def load(self):
        if not os.path.exists(self.file_path):
            return []
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[Memory] JSON 加载失败: {e}")
            return []

    def save(self, data):
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Memory] JSON 保存失败: {e}")
