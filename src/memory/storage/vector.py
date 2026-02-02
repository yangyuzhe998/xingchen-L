import os
import chromadb
from chromadb.utils import embedding_functions

class ChromaStorage:
    """
    ChromaDB 向量存储服务
    """
    def __init__(self, db_path):
        self.client = None
        self.collection = None
        self.skill_collection = None
        
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
            print("[Memory] ChromaDB 向量数据库 (Memory & Skills) 初始化成功。")
        except Exception as e:
            print(f"[Memory] ChromaDB 初始化失败: {e}")

    def get_memory_collection(self):
        return self.collection

    def get_skill_collection(self):
        return self.skill_collection
