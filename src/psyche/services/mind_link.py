import json
import os
import threading
import time
from typing import Optional, Dict
from src.config.settings.settings import settings

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
    
    def __init__(self, storage_path: str = None):
        if storage_path is None:
            self.storage_path = settings.MIND_LINK_STORAGE_PATH
        else:
            self.storage_path = storage_path
            
        self._lock = threading.Lock()
        self._buffer = self._load_buffer()

    def _load_buffer(self) -> Dict:
        """加载持久化的直觉缓冲"""
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)

        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[MindLink] Load buffer failed: {e}")
                
        # 默认空状态
        return {
            "intuition": "保持警惕，注意观察用户意图。", # 默认直觉
            "timestamp": 0,
            "source": "init"
        }

    def _save_buffer(self):
        """保存缓冲"""
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(self._buffer, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[MindLink] Save buffer failed: {e}")

    def inject_intuition(self, content: str, source: str = "navigator"):
        """
        [S-Brain Write] 注入直觉
        S 脑分析完后调用此方法，修改 F 脑的潜意识。
        """
        with self._lock:
            self._buffer = {
                "intuition": content,
                "timestamp": time.time(),
                "source": source
            }
            self._save_buffer()
            print(f"[MindLink] ⚡ 直觉注入: {content[:30]}...")

    def read_intuition(self) -> str:
        """
        [F-Brain Read] 读取直觉
        F 脑在 think() 开始时调用。
        """
        with self._lock:
            # 可以加入衰减逻辑：如果直觉太旧了（比如超过 1 小时），是否还生效？
            # 目前简化：永久生效，直到被覆盖。
            return self._buffer.get("intuition", "")
