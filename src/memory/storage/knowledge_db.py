"""
知识库存储模块 (Knowledge Database)
通过 Mixin 模式聚合基础连接、事实存储、实体管理与图谱操作
"""

from typing import Optional

from src.memory.storage.knowledge.base import KnowledgeBase
from src.memory.storage.knowledge.knowledge_store import KnowledgeStoreMixin
from src.memory.storage.knowledge.entity_store import EntityStoreMixin
from src.memory.storage.knowledge.graph_store import GraphStoreMixin


class KnowledgeDB(KnowledgeBase, KnowledgeStoreMixin, EntityStoreMixin, GraphStoreMixin):
    """
    知识库 (Knowledge Database)
    聚合所有存储功能，保持对外接口 100% 兼容
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(KnowledgeDB, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized") and self._initialized:
            return

        self._initialize_db()
        self._initialized = True


_knowledge_db_instance: Optional[KnowledgeDB] = None


def get_knowledge_db() -> KnowledgeDB:
    """获取全局 KnowledgeDB 实例（延迟初始化）。"""
    global _knowledge_db_instance
    if _knowledge_db_instance is None:
        _knowledge_db_instance = KnowledgeDB()
    return _knowledge_db_instance


class _KnowledgeDBProxy(KnowledgeDB):
    """延迟初始化代理类（继承以通过 isinstance 检查）。"""

    def __init__(self):
        # 覆盖父类 __init__，防止 import 时触发数据库初始化
        pass

    def __getattribute__(self, name):
        if name in ("__class__", "__instancecheck__", "__subclasscheck__"):
            return super().__getattribute__(name)
        return getattr(get_knowledge_db(), name)


# 全局代理（保持原 import 使用方式不变）
knowledge_db = _KnowledgeDBProxy()
