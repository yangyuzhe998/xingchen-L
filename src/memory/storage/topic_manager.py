"""
话题管理器 (Topic Manager)
实现层级记忆架构: Topic → Task → Fragment
"""
from datetime import datetime
from typing import List, Dict, Optional, Any
from src.utils.logger import logger
from src.config.settings.settings import settings
import chromadb
import os
import hashlib


class TopicManager:
    """
    话题管理器
    管理层级记忆: Topic (话题) → Task (任务) → Fragment (片段)
    
    层级结构:
    - Topic: 最高层，代表一个主题领域 (如 "项目讨论", "学习Python")
    - Task: 中间层，具体的子任务 (如 "需求评审", "调试bug")
    - Fragment: 最底层，具体的记忆内容 (带时间戳和情感标签)
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TopicManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        # 使用独立的 ChromaDB 路径
        db_path = os.path.join(settings.MEMORY_DATA_DIR, "topic_db")
        os.makedirs(db_path, exist_ok=True)
        
        self.client = chromadb.PersistentClient(path=db_path)
        
        # 创建三个层级的 Collection
        self.topics = self.client.get_or_create_collection(
            name="topics",
            metadata={"hnsw:space": "cosine", "description": "话题层"}
        )
        
        self.tasks = self.client.get_or_create_collection(
            name="tasks",
            metadata={"hnsw:space": "cosine", "description": "任务层"}
        )
        
        self.fragments = self.client.get_or_create_collection(
            name="fragments",
            metadata={"hnsw:space": "cosine", "description": "片段层"}
        )
        
        self._initialized = True
        logger.info(f"[TopicManager] Initialized with {self.get_stats()}")
    
    # ============ Topic 操作 ============
    
    def create_topic(self, name: str, description: str = None) -> str:
        """
        创建话题
        :param name: 话题名称
        :param description: 话题描述
        :return: 话题 ID
        """
        topic_id = f"topic_{self._generate_id(name)}"
        
        # 检查是否已存在
        existing = self.topics.get(ids=[topic_id])
        if existing["ids"]:
            logger.info(f"[TopicManager] Topic already exists: {name}")
            return topic_id
        
        self.topics.add(
            ids=[topic_id],
            documents=[description or name],
            metadatas=[{
                "name": name,
                "created_at": datetime.now().isoformat(),
                "type": "topic"
            }]
        )
        
        logger.info(f"[TopicManager] Created topic: {name} ({topic_id})")
        return topic_id
    
    def get_topic(self, topic_id: str) -> Optional[Dict]:
        """获取话题详情"""
        result = self.topics.get(ids=[topic_id])
        if result["ids"]:
            return {
                "id": result["ids"][0],
                "document": result["documents"][0],
                "metadata": result["metadatas"][0]
            }
        return None
    
    def search_topics(self, query: str, limit: int = 5) -> List[Dict]:
        """语义搜索话题"""
        results = self.topics.query(
            query_texts=[query],
            n_results=limit
        )
        
        formatted = self._format_query_results(results)
        logger.debug(f"[TopicManager] search_topics('{query}') returned {len(formatted)} results")
        return formatted
    
    # ============ Task 操作 ============
    
    def create_task(self, topic_id: str, name: str, description: str = None) -> str:
        """
        创建任务 (属于某个话题)
        :param topic_id: 所属话题 ID
        :param name: 任务名称
        :param description: 任务描述
        :return: 任务 ID
        """
        task_id = f"task_{self._generate_id(f'{topic_id}_{name}')}"
        
        # 检查是否已存在
        existing = self.tasks.get(ids=[task_id])
        if existing["ids"]:
            logger.info(f"[TopicManager] Task already exists: {name}")
            return task_id
        
        self.tasks.add(
            ids=[task_id],
            documents=[description or name],
            metadatas=[{
                "name": name,
                "topic_id": topic_id,
                "created_at": datetime.now().isoformat(),
                "type": "task"
            }]
        )
        
        logger.info(f"[TopicManager] Created task: {name} under {topic_id}")
        return task_id
    
    def get_tasks_by_topic(self, topic_id: str) -> List[Dict]:
        """获取话题下的所有任务"""
        results = self.tasks.get(
            where={"topic_id": topic_id}
        )
        
        formatted = self._format_get_results(results)
        logger.debug(f"[TopicManager] get_tasks_by_topic('{topic_id}') returned {len(formatted)} tasks")
        return formatted
    
    # ============ Fragment 操作 ============
    
    def add_fragment(self, content: str, topic_id: str = None, task_id: str = None,
                     emotion_tag: str = "neutral", category: str = "memory",
                     meta: Dict = None) -> str:
        """
        添加记忆片段
        :param content: 内容
        :param topic_id: 所属话题 ID (可选)
        :param task_id: 所属任务 ID (可选)
        :param emotion_tag: 情感标签
        :param category: 分类 (memory, knowledge, preference)
        :param meta: 额外元数据
        :return: 片段 ID
        """
        fragment_id = f"frag_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self._generate_id(content[:50])}"
        
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "emotion_tag": emotion_tag,
            "category": category,
            "type": "fragment"
        }
        
        # 添加层级信息
        if topic_id:
            metadata["topic_id"] = topic_id
        if task_id:
            metadata["task_id"] = task_id
        
        # 合并额外元数据
        if meta:
            metadata.update(meta)
        
        self.fragments.add(
            ids=[fragment_id],
            documents=[content],
            metadatas=[metadata]
        )
        
        logger.debug(f"[TopicManager] Added fragment: {content[:30]}...")
        return fragment_id
    
    def search_fragments(self, query: str, limit: int = 10,
                         topic_id: str = None, task_id: str = None,
                         category: str = None, emotion_tag: str = None) -> List[Dict]:
        """
        语义搜索记忆片段 (支持层级过滤)
        """
        where_filter = {}
        
        if topic_id:
            where_filter["topic_id"] = topic_id
        if task_id:
            where_filter["task_id"] = task_id
        if category:
            where_filter["category"] = category
        if emotion_tag:
            where_filter["emotion_tag"] = emotion_tag
        
        results = self.fragments.query(
            query_texts=[query],
            n_results=limit,
            where=where_filter if where_filter else None
        )
        
        formatted = self._format_query_results(results)
        logger.debug(f"[TopicManager] search_fragments('{query[:20]}...') with filter={where_filter} returned {len(formatted)} results")
        return formatted
    
    def get_fragments_by_topic(self, topic_id: str, limit: int = 50) -> List[Dict]:
        """获取话题下的所有片段"""
        results = self.fragments.get(
            where={"topic_id": topic_id},
            limit=limit
        )
        return self._format_get_results(results)
    
    def get_recent_fragments(self, limit: int = 20) -> List[Dict]:
        """获取最近的记忆片段"""
        # ChromaDB 不直接支持按时间排序，获取所有然后排序
        results = self.fragments.get(limit=limit * 2)  # 获取更多以防排序后不够
        
        items = self._format_get_results(results)
        # 按时间戳倒序排列
        items.sort(key=lambda x: x.get("metadata", {}).get("timestamp", ""), reverse=True)
        
        return items[:limit]
    
    # ============ 辅助方法 ============
    
    def _generate_id(self, text: str) -> str:
        """生成短 ID"""
        return hashlib.md5(text.encode()).hexdigest()[:8]
    
    def _format_query_results(self, results: Dict) -> List[Dict]:
        """格式化 query 结果"""
        items = []
        if results["ids"] and results["ids"][0]:
            for i, id_ in enumerate(results["ids"][0]):
                items.append({
                    "id": id_,
                    "document": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results.get("distances") else None
                })
        return items
    
    def _format_get_results(self, results: Dict) -> List[Dict]:
        """格式化 get 结果"""
        items = []
        if results["ids"]:
            for i, id_ in enumerate(results["ids"]):
                items.append({
                    "id": id_,
                    "document": results["documents"][i] if results["documents"] else "",
                    "metadata": results["metadatas"][i] if results["metadatas"] else {}
                })
        return items
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            "topics": self.topics.count(),
            "tasks": self.tasks.count(),
            "fragments": self.fragments.count()
        }
    
    def clear_all(self):
        """清空所有数据 (危险操作，仅用于测试)"""
        # 删除并重建 collections
        self.client.delete_collection("topics")
        self.client.delete_collection("tasks")
        self.client.delete_collection("fragments")
        
        self.topics = self.client.get_or_create_collection(name="topics")
        self.tasks = self.client.get_or_create_collection(name="tasks")
        self.fragments = self.client.get_or_create_collection(name="fragments")
        
        logger.warning("[TopicManager] All data cleared!")


# 全局实例
topic_manager = TopicManager()
