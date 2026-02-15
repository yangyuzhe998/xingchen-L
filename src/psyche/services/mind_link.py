import json
import os
import threading
import time
from typing import Dict
from src.config.settings.settings import settings
from src.utils.logger import logger


class MindLink:
    """
    心智链路 (Mind-Link) - 全局工作台 (Global Workspace)

    功能：
    1. 存储 S 脑的异步直觉 (Intuition Injection)。
    2. 提供 F 脑的潜意识读取 (Subconscious Reading)。
    3. 充当 F 脑与 S 脑之间的异步消息缓冲。

    实现：
    - 使用内存 + 文件持久化。
    - 线程安全。
    """

    # 直觉衰减阈值（秒）
    INTUITION_WEAKEN_AFTER_SECONDS = 3600  # 1h
    INTUITION_EXPIRE_AFTER_SECONDS = 7200  # 2h

    def __init__(self, storage_path: str = None):
        if storage_path is None:
            self.storage_path = settings.MIND_LINK_STORAGE_PATH
        else:
            self.storage_path = storage_path

        self._lock = threading.Lock()
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
            "timestamp": 0,
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
        """
        [S-Brain Write] 注入直觉
        S 脑分析完后调用此方法，修改 F 脑的潜意识。
        """
        with self._lock:
            self._buffer = {
                "intuition": content,
                "timestamp": time.time(),
                "source": source,
            }
            self._save_buffer()
            logger.info(f"[MindLink] ⚡ 直觉注入: {content[:30]}...")

    def read_intuition(self) -> str:
        """
        [F-Brain Read] 读取直觉（带衰减/过期）

        规则：
        - 超过 INTUITION_EXPIRE_AFTER_SECONDS：认为直觉过期，返回默认值
        - 超过 INTUITION_WEAKEN_AFTER_SECONDS：认为直觉变弱，返回“模糊的直觉”前缀
        - 否则返回原直觉
        """
        with self._lock:
            intuition = self._buffer.get("intuition", "")
            timestamp = self._buffer.get("timestamp", 0) or 0

            if not intuition:
                return ""

            if not timestamp:
                return intuition

            age_seconds = time.time() - float(timestamp)

            if age_seconds >= self.INTUITION_EXPIRE_AFTER_SECONDS:
                return "保持观察，暂无强烈直觉。"

            if age_seconds >= self.INTUITION_WEAKEN_AFTER_SECONDS:
                return f"(模糊的直觉) {intuition}"

            return intuition
