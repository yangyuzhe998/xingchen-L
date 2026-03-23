"""
知识库存储模块 (Knowledge Database)
通过 Mixin 模式聚合基础连接、事实存储、实体管理与图谱操作
"""

from typing import Optional
from xingchen.utils.proxy import lazy_proxy
from xingchen.memory.storage.knowledge.base import KnowledgeBase
from xingchen.memory.storage.knowledge.knowledge_store import KnowledgeStoreMixin
from xingchen.memory.storage.knowledge.entity_store import EntityStoreMixin
from xingchen.memory.storage.knowledge.graph_store import GraphStoreMixin


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


# 全局代理
knowledge_db = lazy_proxy(get_knowledge_db, KnowledgeDB)
