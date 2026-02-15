import os
import chromadb
from chromadb.utils import embedding_functions
from src.utils.logger import logger

class ChromaStorage:
    """
    ChromaDB 向量存储服务
    """
    def __init__(self, db_path):
        self.client = None
        self.collection = None
        self.skill_collection = None
        self.command_docs_collection = None
        self.command_cases_collection = None
        self.alias_collection = None
        self._available = False
        
        try:
            self.client = chromadb.PersistentClient(path=db_path)
            # 使用默认的 embedding 模型
            self.collection = self.client.get_or_create_collection(
                name="long_term_memory",
                metadata={"hnsw:space": "cosine"}
            )
            
            self.skill_collection = self.client.get_or_create_collection(
                name="skill_library",
                metadata={"hnsw:space": "cosine"}
            )
            
            self.command_docs_collection = self.client.get_or_create_collection(
                name="command_docs",
                metadata={"hnsw:space": "cosine"}
            )
            
            self.command_cases_collection = self.client.get_or_create_collection(
                name="command_cases",
                metadata={"hnsw:space": "cosine"}
            )
            
            self.alias_collection = self.client.get_or_create_collection(
                name="entity_aliases",
                metadata={"hnsw:space": "cosine"}
            )
            self._available = True
            logger.info("[Memory] ChromaDB 向量数据库 (Memory & Skills & Docs & Cases & Aliases) 初始化成功。")
        except Exception as e:
            logger.error(f"[Memory] ChromaDB 初始化失败: {e}", exc_info=True)
            logger.warning("[Memory] 向量检索功能将不可用，系统将以降级模式运行。")

    def is_available(self):
        """检查向量库是否可用"""
        return self._available

    def get_memory_collection(self):
        return self.collection if self._available else None

    def get_skill_collection(self):
        return self.skill_collection if self._available else None
        
    def get_alias_collection(self):
        return self.alias_collection if self._available else None

    def get_command_docs_collection(self):
        return self.command_docs_collection if self._available else None

    def get_command_cases_collection(self):
        return self.command_cases_collection if self._available else None
