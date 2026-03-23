import json
import os
from typing import List, Dict, Any, Optional
from xingchen.utils.logger import logger
from xingchen.memory.storage.knowledge_db import knowledge_db, KnowledgeDB

class GraphMemory:
    """
    轻量级知识图谱存储 (GraphRAG) - [Refactored v2]
    底层实现已切换为 KnowledgeDB (SQLite)，不再使用 NetworkX/JSON。
    保留此类作为 Facade 以兼容现有代码。
    """
    def __init__(self, data_path: str = None):
        self.db: KnowledgeDB = knowledge_db

    def load(self):
        """Deprecated: SQLite is persistent, no manual load needed."""
        pass

    def save(self, force=False):
        """Deprecated: SQLite is persistent, no manual save needed."""
        pass

    def add_triplet(self, source: str, relation: str, target: str, weight: float = 1.0, meta: Dict = None, relation_type: str = "general"):
        """
        添加三元组: Source --[relation]--> Target
        """
        self.db.add_edge(source, target, relation, weight, relation_type, meta)

    def get_cognitive_subgraph(self, entity: str, relation_type: str = None) -> List[Dict]:
        """
        获取特定认知维度的子图
        """
        return self.db.get_edges(source=entity, relation_type=relation_type)

    def get_emotional_subgraph(self, entity: str, emotion_tag: str = None) -> List[Dict]:
        """
        获取带有特定情感色彩的记忆子图
        """
        edges = self.db.get_edges(source=entity)
        results = []
        for edge in edges:
            meta = edge.get("meta") or {}
            current_emotion = meta.get("emotion_tag", "neutral")
            
            if emotion_tag and current_emotion != emotion_tag:
                continue
                
            results.append({
                "source": edge["source"],
                "relation": edge["relation"],
                "target": edge["target"],
                "emotion_tag": current_emotion,
                "psyche_context": meta.get("psyche_context", ""),
                "weight": edge["weight"]
            })
        return results

    def search_entity(self, entity: str, depth: int = 1) -> List[Dict]:
        """
        搜索实体及其邻居 (One-hop)
        """
        out_edges = self.db.get_edges(source=entity)
        in_edges = self.db.get_edges(target=entity)
        return out_edges + in_edges

    def get_path(self, source: str, target: str) -> List[str]:
        """
        寻找两个实体之间的最短路径
        """
        queue = [(source, [source])]
        visited = set()
        
        while queue:
            (vertex, path) = queue.pop(0)
            if len(path) > 3: # 限制深度为 3
                continue
                
            if vertex not in visited:
                visited.add(vertex)
                neighbors = self.db.get_related_nodes(vertex, limit=20)
                for neighbor_info in neighbors:
                    neighbor = neighbor_info['neighbor']
                    if neighbor == target:
                        return path + [target]
                    else:
                        queue.append((neighbor, path + [neighbor]))
        return []
