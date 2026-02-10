"""
知识库存储模块 (Knowledge Database)
通过 Mixin 模式聚合基础连接、事实存储、实体管理与图谱操作
"""
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
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        # 初始化基础数据库设置 (路径、连接、Schema)
        self._initialize_db()
        self._initialized = True

# 全局实例，确保单例语义
knowledge_db = KnowledgeDB()
