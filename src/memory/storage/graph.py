import json
import os
import networkx as nx
from datetime import datetime
from typing import List, Dict, Any, Optional

class GraphMemory:
    """
    轻量级知识图谱存储 (GraphRAG)
    基于 NetworkX 和 JSON 实现。
    """
    def __init__(self, data_path: str):
        self.data_path = data_path
        self.graph = nx.MultiDiGraph() # 使用多重有向图，允许两个节点间存在多种关系
        self._dirty = False # Dirty Check Flag
        self.load()

    def load(self):
        """从 JSON 加载图谱"""
        if os.path.exists(self.data_path):
            try:
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 使用 node_link_graph 还原
                    self.graph = nx.node_link_graph(data, directed=True, multigraph=True)
                    print(f"[GraphMemory] Loaded {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges.")
            except Exception as e:
                print(f"[GraphMemory] Load failed: {e}. Initializing empty graph.")
                self.graph = nx.MultiDiGraph()
        else:
            print("[GraphMemory] No existing data. Initializing empty graph.")
        self._dirty = False

    def save(self, force=False):
        """
        保存图谱到 JSON
        :param force: 是否强制保存 (忽略 dirty 标志)
        """
        if not self._dirty and not force:
            return

        try:
            data = nx.node_link_data(self.graph)
            # Fix: os.path.dirname("file.json") returns empty string on Windows, causing makedirs to fail
            dir_name = os.path.dirname(self.data_path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)
            
            with open(self.data_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # Reset dirty flag
            self._dirty = False
            # print(f"[GraphMemory] Saved to {self.data_path}")
        except Exception as e:
            print(f"[GraphMemory] Save failed: {e}")

    def add_triplet(self, source: str, relation: str, target: str, weight: float = 1.0, meta: Dict = None, relation_type: str = "general"):
        """
        添加三元组: Source --[relation]--> Target
        relation_type: 'social' (社交), 'causal' (因果), 'temporal' (时间), 'attribute' (属性), 'general' (通用)
        """
        self._dirty = True # Mark as dirty
        
        # 确保节点存在
        if not self.graph.has_node(source):
            self.graph.add_node(source, type="entity")
        if not self.graph.has_node(target):
            self.graph.add_node(target, type="entity")
            
        # 添加边
        timestamp = datetime.now().isoformat()
        # 允许更新现有边的权重，或添加新类型的边
        # NetworkX MultiDiGraph 允许两点间多条边，这里我们简单处理：如果是同一种关系，更新权重和时间
        
        # 检查是否已存在同名关系
        existing_key = None
        if self.graph.has_edge(source, target):
            for key, data in self.graph[source][target].items():
                if data.get("relation") == relation:
                    existing_key = key
                    break
        
        if existing_key is not None:
            # 更新现有关系
            self.graph[source][target][existing_key]['weight'] = weight
            self.graph[source][target][existing_key]['timestamp'] = timestamp
            if meta:
                self.graph[source][target][existing_key]['meta'].update(meta)
        else:
            # 添加新关系
            self.graph.add_edge(source, target, relation=relation, relation_type=relation_type, weight=weight, timestamp=timestamp, meta=meta or {})
            
        # 移除自动 save，改为手动或 periodic save
        # self.save()

    def get_cognitive_subgraph(self, entity: str, relation_type: str = None) -> List[Dict]:
        """
        获取特定认知维度的子图 (例如：只看社交关系)
        """
        if not self.graph.has_node(entity):
            return []
            
        results = []
        # 仅遍历出边
        for _, target, data in self.graph.out_edges(entity, data=True):
            if relation_type and data.get("relation_type") != relation_type:
                continue
                
            results.append({
                "source": entity,
                "relation": data.get("relation"),
                "relation_type": data.get("relation_type"),
                "target": target,
                "weight": data.get("weight"),
                "meta": data.get("meta")
            })
        return results

    def get_emotional_subgraph(self, entity: str, emotion_tag: str = None) -> List[Dict]:
        """
        获取带有特定情感色彩的记忆子图
        """
        if not self.graph.has_node(entity):
            return []
            
        results = []
        for _, target, data in self.graph.out_edges(entity, data=True):
            # Check meta for emotion_tag
            meta = data.get("meta", {})
            current_emotion = meta.get("emotion_tag", "neutral")
            
            if emotion_tag and current_emotion != emotion_tag:
                continue
                
            results.append({
                "source": entity,
                "relation": data.get("relation"),
                "target": target,
                "emotion_tag": current_emotion,
                "psyche_context": meta.get("psyche_context", ""),
                "weight": data.get("weight")
            })
        return results

    def search_entity(self, entity: str, depth: int = 1) -> List[Dict]:
        """
        搜索实体及其邻居 (One-hop / Multi-hop)
        """
        if not self.graph.has_node(entity):
            return []
            
        results = []
        # 获取出边 (主动关系)
        for _, target, data in self.graph.out_edges(entity, data=True):
            results.append({
                "source": entity,
                "relation": data.get("relation"),
                "target": target,
                "weight": data.get("weight"),
                "meta": data.get("meta")
            })
            
        # 获取入边 (被动关系)
        for source, _, data in self.graph.in_edges(entity, data=True):
             results.append({
                "source": source,
                "relation": data.get("relation"),
                "target": entity,
                "weight": data.get("weight"),
                "meta": data.get("meta")
            })
            
        return results

    def get_path(self, source: str, target: str) -> List[str]:
        """寻找两个实体之间的最短路径"""
        try:
            return nx.shortest_path(self.graph, source, target)
        except nx.NetworkXNoPath:
            return []
        except nx.NodeNotFound:
            return []

# Singleton instance (Lazy load)
_graph_instance = None

def get_graph_memory():
    global _graph_instance
    if _graph_instance is None:
        from src.config.settings.settings import settings
        # 假设 settings 中定义了 GRAPH_DB_PATH
        graph_path = os.path.join(settings.MEMORY_DATA_DIR, "knowledge_graph.json")
        _graph_instance = GraphMemory(graph_path)
    return _graph_instance
