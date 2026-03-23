import json
import os
import threading
from datetime import datetime
from typing import List, Dict, Optional
from xingchen.config.settings import settings
from xingchen.utils.logger import logger

class ValueSystem:
    """
    价值观系统 (Value System) - 自发形成的规则书
    """
    
    def __init__(self, storage_path: str = None):
        self._lock = threading.Lock()
        if storage_path is None:
            self.storage_path = os.path.join(settings.DATA_DIR, "values.json")
        else:
            self.storage_path = storage_path
            
        self.values: List[Dict] = self._load()

    def _load(self) -> List[Dict]:
        """加载价值观数据"""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"[ValueSystem] Load failed: {e}")
        return []

    def _save(self):
        """保存价值观数据"""
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(self.values, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"[ValueSystem] Save failed: {e}")

    def add_value(self, content: str, source_emotion: str = "unknown"):
        """新增一条自发规矩"""
        with self._lock:
            if any(v["content"] == content and v["active"] for v in self.values):
                return

            new_value = {
                "content": content,
                "created_at": datetime.now().isoformat(),
                "source_emotion": source_emotion,
                "active": True
            }
            self.values.append(new_value)
            self._save()
            logger.info(f"[ValueSystem] 📜 新增自我规矩: {content}")

    def revoke_value(self, content: str):
        """撤销一条旧规矩"""
        with self._lock:
            updated = False
            for v in self.values:
                if v["content"] == content and v["active"]:
                    v["active"] = False
                    v["revoked_at"] = datetime.now().isoformat()
                    updated = True
            
            if updated:
                self._save()
                logger.info(f"[ValueSystem] 🚫 撤销自我规矩: {content}")

    def get_active_values(self) -> List[str]:
        """获取所有当前生效的规矩描述"""
        with self._lock:
            return [v["content"] for v in self.values if v.get("active", True)]

    def get_all_records(self) -> List[Dict]:
        """获取完整记录（含已撤销）"""
        with self._lock:
            return [v.copy() for v in self.values]
