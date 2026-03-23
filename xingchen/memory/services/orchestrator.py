"""
记忆协调器 (Memory Orchestrator)
协调层级记忆存储和自动分类
"""
from typing import List, Dict, Optional
from xingchen.utils.logger import logger
from xingchen.memory.storage.topic_manager import topic_manager
from xingchen.memory.services.auto_classifier import auto_classifier
import json
import os
from datetime import datetime
from xingchen.config.settings import settings
from xingchen.utils.proxy import lazy_proxy


class MemoryOrchestrator:
    """
    记忆协调器
    在 S脑压缩周期中协调层级记忆存储
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MemoryOrchestrator, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self.auto_classifier = auto_classifier
        self.pending_path = os.path.join(settings.DATA_DIR, "classification_pending.json")
        self._initialized = True
        logger.info("[MemoryOrchestrator] Initialized")
        
        # 启动时重试未完成的分类
        self._retry_pending()
    
    def classify_compressed_memory(self, script: str) -> Dict:
        """
        分类压缩后的记忆
        """
        if not script or len(script) < 50:
            logger.debug("[MemoryOrchestrator] 脚本太短，跳过分类")
            return {"success": 0, "failed": 0}
        
        self._add_pending(script)
        
        try:
            fragment_id = self.auto_classifier.classify_and_store(
                content=script,
                category="conversation"
            )
            
            self._clear_pending()
            
            logger.info(f"[MemoryOrchestrator] 分类成功: {fragment_id}")
            return {"success": 1, "failed": 0, "fragment_id": fragment_id}
            
        except Exception as e:
            logger.warning(f"[MemoryOrchestrator] 分类失败 (将在下次启动时重试): {e}")
            return {"success": 0, "failed": 1, "error": str(e)}
    
    def _add_pending(self, content: str):
        try:
            data = {
                "content": content[:2000],
                "timestamp": datetime.now().isoformat()
            }
            with open(self.pending_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"[MemoryOrchestrator] 写入待处理失败: {e}")
    
    def _clear_pending(self):
        try:
            if os.path.exists(self.pending_path):
                os.remove(self.pending_path)
        except Exception as e:
            logger.warning(f"[MemoryOrchestrator] 清除待处理失败: {e}")

    def _retry_pending(self):
        if not os.path.exists(self.pending_path):
            return
            
        try:
            with open(self.pending_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            content = data.get("content")
            if content:
                logger.info(f"[MemoryOrchestrator] 正在重试上次未完成的分类...")
                self.classify_compressed_memory(content)
        except Exception as e:
            logger.warning(f"[MemoryOrchestrator] 重试失败: {e}")


_orchestrator_instance: Optional[MemoryOrchestrator] = None


def get_orchestrator() -> MemoryOrchestrator:
    """获取全局 MemoryOrchestrator 实例（延迟初始化）。"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = MemoryOrchestrator()
    return _orchestrator_instance


orchestrator = lazy_proxy(get_orchestrator, MemoryOrchestrator)
