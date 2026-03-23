import json
import os
from typing import List, Dict, Any
from xingchen.utils.logger import logger

class JsonStorage:
    """
    JSON 文件存储服务 (长期记忆)
    """
    def __init__(self, file_path):
        self.file_path = file_path
        self._ensure_dir()

    def _ensure_dir(self):
        dir_name = os.path.dirname(self.file_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

    def load(self) -> List[Dict[str, Any]]:
        """
        加载 JSON 数据
        """
        if not os.path.exists(self.file_path):
            return []
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict):
                    return [data]
                else:
                    logger.warning(f"[Memory] 意外的数据类型: {type(data)}，返回空列表")
                    return []
        except Exception as e:
            logger.error(f"[Memory] JSON 加载失败: {e}", exc_info=True)
            return []

    def save(self, data: List[Dict[str, Any]]) -> None:
        """
        [Atomic Write] 使用原子写入防止数据损坏
        """
        temp_path = f"{self.file_path}.tmp"
        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            os.replace(temp_path, self.file_path)
            
        except Exception as e:
            logger.error(f"[Memory] JSON 保存失败: {e}", exc_info=True)
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
