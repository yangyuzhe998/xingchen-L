"""
话题管理器 (Topic Manager)
实现层级记忆架构: Topic → Task → Fragment
"""

from datetime import datetime
from typing import List, Dict, Optional, Any
import os
import hashlib
from xingchen.utils.logger import logger
from xingchen.config.settings import settings
from xingchen.utils.proxy import lazy_proxy
import chromadb


class TopicManager:
    """
    话题管理器
    管理层级记忆: Topic (话题) → Task (任务) → Fragment (片段)
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TopicManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized") and self._initialized:
            return

        db_path = os.path.join(settings.DATA_DIR, "topic_db")
        os.makedirs(db_path, exist_ok=True)

        self.client = chromadb.PersistentClient(path=db_path)

        self.topics = self.client.get_or_create_collection(
            name="topics",
            metadata={"hnsw:space": "cosine", "description": "话题层"},
        )

        self.tasks = self.client.get_or_create_collection(
            name="tasks",
            metadata={"hnsw:space": "cosine", "description": "任务层"},
        )

        self.fragments = self.client.get_or_create_collection(
            name="fragments",
            metadata={"hnsw:space": "cosine", "description": "片段层"},
        )

        self._initialized = True
        logger.info(f"[TopicManager] Initialized with {self.get_stats()}")

    def _generate_id(self, text: str) -> str:
        """生成唯一 ID"""
        return hashlib.md5(text.encode()).hexdigest()[:8]

    def create_topic(self, name: str, description: str = None) -> str:
        """创建话题"""
        topic_id = f"topic_{self._generate_id(name)}"

        try:
            existing = self.topics.get(ids=[topic_id])
            if existing and existing.get("ids") and len(existing["ids"]) > 0:
                return topic_id
        except Exception:
            pass

        self.topics.add(
            ids=[topic_id],
            documents=[description or name],
            metadatas=[
                {
                    "name": name,
                    "created_at": datetime.now().isoformat(),
                    "type": "topic",
                }
            ],
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
        results = self.topics.query(query_texts=[query], n_results=limit)
        return self._format_query_results(results)

    def create_task(self, topic_id: str, name: str, description: str = None) -> str:
        """创建任务 (属于某个话题)"""
        task_id = f"task_{self._generate_id(f'{topic_id}_{name}')}"

        existing = self.tasks.get(ids=[task_id])
        if existing["ids"]:
            return task_id

        self.tasks.add(
            ids=[task_id],
            documents=[description or name],
            metadatas=[
                {
                    "name": name,
                    "topic_id": topic_id,
                    "created_at": datetime.now().isoformat(),
                    "type": "task",
                }
            ],
        )

        logger.info(f"[TopicManager] Created task: {name} under {topic_id}")
        return task_id

    def add_fragment(
        self,
        content: str,
        topic_id: str = None,
        task_id: str = None,
        emotion_tag: str = "neutral",
        category: str = "memory",
        meta: Dict = None,
    ) -> str:
        """添加记忆片段"""
        seed = f"{category}:{topic_id or 'none'}:{task_id or 'none'}:{content}"
        fingerprint = hashlib.md5(seed.encode()).hexdigest()[:12]
        fragment_id = f"frag_{datetime.now().strftime('%Y%m%d')}_{fingerprint}"

        existing = self.fragments.get(ids=[fragment_id])

        if existing and existing["ids"] and len(existing["ids"]) > 0:
            old_meta = existing["metadatas"][0]
            count = old_meta.get("mention_count", 1) + 1
            weight = min(2.0, old_meta.get("weight", 1.0) + 0.1)

            updated_meta = {
                **old_meta,
                "last_activated": datetime.now().isoformat(),
                "mention_count": count,
                "weight": weight,
            }
            if meta:
                updated_meta.update(meta)

            self.fragments.update(ids=[fragment_id], metadatas=[updated_meta])
            return fragment_id

        metadata = {
            "created_at": datetime.now().isoformat(),
            "last_activated": datetime.now().isoformat(),
            "mention_count": 1,
            "weight": 1.0,
            "emotion_tag": emotion_tag,
            "category": category,
            "type": "fragment",
            "fingerprint": fingerprint,
            "topic_id": topic_id or "none",
            "task_id": task_id or "none",
        }

        if meta:
            metadata.update(meta)

        self.fragments.add(ids=[fragment_id], documents=[content], metadatas=[metadata])
        return fragment_id

    def _format_query_results(self, results: Dict) -> List[Dict]:
        items = []
        if results["ids"] and results["ids"][0]:
            for i, id_ in enumerate(results["ids"][0]):
                items.append(
                    {
                        "id": id_,
                        "document": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "distance": results["distances"][0][i] if results.get("distances") else None,
                    }
                )
        return items

    def _format_get_results(self, results: Dict) -> List[Dict]:
        items = []
        if results["ids"]:
            for i, id_ in enumerate(results["ids"]):
                items.append(
                    {
                        "id": id_,
                        "document": results["documents"][i] if results["documents"] else "",
                        "metadata": results["metadatas"][i] if results["metadatas"] else {},
                    }
                )
        return items

    def get_stats(self):
        return {
            "topics": self.topics.count(),
            "tasks": self.tasks.count(),
            "fragments": self.fragments.count()
        }

    def get_recent_fragments(self, limit: int = 5) -> List[Dict]:
        """获取最近活跃的记忆片段"""
        # 注意：ChromaDB 默认不支持按元数据排序，这里获取最近的一些片段并在内存中排序
        # 这是一个简化实现，生产环境下可能需要更复杂的索引
        results = self.fragments.get(limit=limit * 10) # 多取一点
        items = self._format_get_results(results)
        
        # 按 last_activated 降序排序
        items.sort(key=lambda x: x["metadata"].get("last_activated", ""), reverse=True)
        return items[:limit]


_topic_manager_instance: Optional[TopicManager] = None


def get_topic_manager() -> TopicManager:
    """获取全局 TopicManager 实例（延迟初始化）。"""
    global _topic_manager_instance
    if _topic_manager_instance is None:
        _topic_manager_instance = TopicManager()
    return _topic_manager_instance


topic_manager = lazy_proxy(get_topic_manager, TopicManager)
