"""
记忆协调器 (Memory Orchestrator)
协调层级记忆存储和自动分类

设计决策:
- 只在 S脑压缩时触发分类 (非每次 add_long_term)
- 使用 WAL 实现失败重试 (基于 replay 模式)
- 与 MemoryService 解耦
"""
from typing import List, Dict, Optional
from src.utils.logger import logger
from src.memory.storage.topic_manager import topic_manager
from src.memory.services.auto_classifier import auto_classifier
import json
import os
from datetime import datetime
from src.config.settings.settings import settings


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
        
        # 依赖注入 (方便测试)
        self.auto_classifier = auto_classifier
        
        # 分类专用待处理文件 (简化版 WAL)
        self.pending_path = os.path.join(settings.MEMORY_DATA_DIR, "classification_pending.json")
        self._initialized = True
        logger.info("[MemoryOrchestrator] Initialized")
        
        # 启动时重试未完成的分类
        self._retry_pending()
    
    def classify_compressed_memory(self, script: str) -> Dict:
        """
        分类压缩后的记忆 (由 Compressor 调用)
        
        :param script: 压缩的对话脚本
        :return: 分类结果
        """
        if not script or len(script) < 50:
            logger.debug("[MemoryOrchestrator] 脚本太短，跳过分类")
            return {"success": 0, "failed": 0}
        
        # 1. 先记录到待处理 (失败后可重试)
        self._add_pending(script)
        
        try:
            # 2. 调用分类器
            fragment_id = self.auto_classifier.classify_and_store(
                content=script,
                category="conversation"
            )
            
            # 3. 成功后清除待处理
            self._clear_pending()
            
            logger.info(f"[MemoryOrchestrator] 分类成功: {fragment_id}")
            return {"success": 1, "failed": 0, "fragment_id": fragment_id}
            
        except Exception as e:
            logger.warning(f"[MemoryOrchestrator] 分类失败 (将在下次启动时重试): {e}")
            return {"success": 0, "failed": 1, "error": str(e)}
    
    def _add_pending(self, content: str):
        """添加到待处理"""
        try:
            data = {
                "content": content[:2000],  # 截断避免文件过大
                "timestamp": datetime.now().isoformat()
            }
            with open(self.pending_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"[MemoryOrchestrator] 写入待处理失败: {e}")
    
    def _clear_pending(self):
        """清除待处理"""
        try:
            if os.path.exists(self.pending_path):
                os.remove(self.pending_path)
        except Exception as e:
            logger.warning(f"[MemoryOrchestrator] 清除待处理失败: {e}")

    def _retry_pending(self):
        """重试未完成的分类"""
        if not os.path.exists(self.pending_path):
            return
        
        try:
            with open(self.pending_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            content = data.get("content", "")
            if not content:
                self._clear_pending()
                return
            
            logger.info(f"[MemoryOrchestrator] 发现未完成的分类任务，开始重试...")
            
            fragment_id = self.auto_classifier.classify_and_store(
                content=content,
                category="conversation"
            )
            
            self._clear_pending()
            logger.info(f"[MemoryOrchestrator] 重试成功: {fragment_id}")
            
        except Exception as e:
            logger.warning(f"[MemoryOrchestrator] 重试失败: {e}")
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        has_pending = os.path.exists(self.pending_path)
        return {
            "topic_manager": topic_manager.get_stats(),
            "has_pending": has_pending
        }


_memory_orchestrator_instance: Optional[MemoryOrchestrator] = None


def get_memory_orchestrator() -> MemoryOrchestrator:
    """获取全局 MemoryOrchestrator 实例（延迟初始化）。"""
    global _memory_orchestrator_instance
    if _memory_orchestrator_instance is None:
        _memory_orchestrator_instance = MemoryOrchestrator()
    return _memory_orchestrator_instance


class _MemoryOrchestratorProxy(MemoryOrchestrator):
    """延迟初始化代理类（继承以通过 isinstance 检查）。"""

    def __init__(self):
        # 覆盖父类 __init__，防止 import 时触发重试逻辑或日志
        pass

    def __getattribute__(self, name):
        if name in ("__class__", "__instancecheck__", "__subclasscheck__"):
            return super().__getattribute__(name)
        return getattr(get_memory_orchestrator(), name)


# 全局实例（保持原 import 使用方式不变）
memory_orchestrator = _MemoryOrchestratorProxy()
