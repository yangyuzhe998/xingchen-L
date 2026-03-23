import json
import os
import threading
import time
from typing import Dict, Optional
from xingchen.config.settings import settings
from xingchen.utils.logger import logger


class MindLink:
    """
    心智链路 (Mind-Link) - 全局工作台 (Global Workspace)
    """

    def __init__(self, storage_path: str = None):
        if storage_path is None:
            self.storage_path = settings.MIND_LINK_STORAGE_PATH
        else:
            self.storage_path = storage_path

        self._lock = threading.Lock()
        
        # 从 settings 获取配置
        self.INTUITION_WEAKEN_AFTER_SECONDS = settings.INTUITION_WEAKEN_SECONDS
        self.INTUITION_EXPIRE_AFTER_SECONDS = settings.EXPIRE_SECONDS
        
        self._buffer = self._load_buffer()

    def _load_buffer(self) -> Dict:
        """加载持久化的直觉缓冲"""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)

        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"[MindLink] Load buffer failed: {e}", exc_info=True)

        return {
            "intuition": "保持警惕，注意观察用户意图。",
            "timestamp": time.time(),
            "source": "init",
        }

    def _save_buffer(self):
        """保存缓冲"""
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(self._buffer, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"[MindLink] Save buffer failed: {e}", exc_info=True)

    def inject_intuition(self, content: str, source: str = "navigator"):
        """注入直觉"""
        with self._lock:
            self._buffer = {
                "intuition": content,
                "timestamp": time.time(),
                "source": source,
            }
            self._save_buffer()
            logger.info(f"[MindLink] ⚡ 直觉注入: {content[:30]}...")

    def read_intuition(self) -> str:
        """读取直觉（带衰减/过期）"""
        with self._lock:
            intuition = self._buffer.get("intuition", "")
            timestamp = self._buffer.get("timestamp", 0) or 0

            if not intuition:
                return ""

            age_seconds = time.time() - float(timestamp)

            if age_seconds >= self.INTUITION_EXPIRE_AFTER_SECONDS:
                return "保持观察，暂无强烈直觉。"

            if age_seconds >= self.INTUITION_WEAKEN_AFTER_SECONDS:
                return f"模糊的直觉：{intuition}"

            return intuition
