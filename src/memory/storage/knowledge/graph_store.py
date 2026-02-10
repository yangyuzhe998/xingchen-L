import json
import sqlite3
from datetime import datetime
from typing import List, Dict
from src.utils.logger import logger

class GraphStoreMixin:
    """
    知识库图谱操作 Mixin (Spider Web Memory)
    """
    def add_node(self, name: str, type: str = "concept", weight: float = 1.0, meta: Dict = None):
        """添加或更新图节点"""
        meta_json = json.dumps(meta, ensure_ascii=False) if meta else None
        with self._get_conn() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO nodes (name, type, weight, meta, last_activated)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(name) DO UPDATE SET
                        weight = excluded.weight,
                        last_activated = CURRENT_TIMESTAMP
                ''', (name, type, weight, meta_json))
                conn.commit()
                return True
            except Exception as e:
                logger.error(f"[KnowledgeDB] Failed to add node {name}: {e}")
                return False

    def add_edge(self, source: str, target: str, relation: str = "RELATED_TO", 
                 weight: float = 1.0, relation_type: str = "general", meta: Dict = None):
        """添加或更新边 (自动创建缺失的节点)"""
        self.add_node(source)
        self.add_node(target)
        meta_json = json.dumps(meta, ensure_ascii=False) if meta else None
        with self._get_conn() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO edges (source, target, relation, relation_type, weight, meta, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(source, target, relation) DO UPDATE SET
                        weight = excluded.weight,
                        relation_type = excluded.relation_type,
                        meta = excluded.meta
                ''', (source, target, relation, relation_type, weight, meta_json))
                conn.commit()
                return True
            except Exception as e:
                logger.error(f"[KnowledgeDB] Failed to add edge {source}->{target}: {e}")
                return False

    def get_edges(self, source: str = None, target: str = None, relation_type: str = None, limit: int = 100) -> List[Dict]:
        """获取边列表"""
        with self._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            query = "SELECT * FROM edges WHERE 1=1"
            params = []
            if source:
                query += " AND source = ?"
                params.append(source)
            if target:
                query += " AND target = ?"
                params.append(target)
            if relation_type:
                query += " AND relation_type = ?"
                params.append(relation_type)
            query += " ORDER BY weight DESC LIMIT ?"
            params.append(limit)
            cursor.execute(query, params)
            rows = cursor.fetchall()
            results = []
            for row in rows:
                result = dict(row)
                if result.get('meta'):
                    try:
                        result['meta'] = json.loads(result['meta'])
                    except:
                        result['meta'] = {}
                else:
                    result['meta'] = {}
                results.append(result)
            return results

    def get_related_nodes(self, node_name: str, min_weight: float = 0.5, limit: int = 10) -> List[Dict]:
        """获取相关联的节点 (扩散激活)"""
        with self._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            query = '''
                SELECT 'out' as direction, target as neighbor, relation, weight 
                FROM edges WHERE source = ? AND weight >= ?
                UNION
                SELECT 'in' as direction, source as neighbor, relation, weight 
                FROM edges WHERE target = ? AND weight >= ?
                ORDER BY weight DESC
                LIMIT ?
            '''
            cursor.execute(query, (node_name, min_weight, node_name, min_weight, limit))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def find_nodes_in_text(self, text: str) -> List[str]:
        """从文本中查找已知的节点 (Entity Linking)"""
        if not text: return []
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT name FROM nodes 
                WHERE LENGTH(name) > 1 AND instr(?, name) > 0
                ORDER BY length(name) DESC
                LIMIT 5
            ''', (text,))
            rows = cursor.fetchall()
            return [row[0] for row in rows]

    def get_stats(self) -> Dict:
        """获取数据库统计信息"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM knowledge')
            knowledge_count = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM entities')
            entity_count = cursor.fetchone()[0]
            cursor.execute('SELECT category, COUNT(*) FROM knowledge GROUP BY category')
            categories = {row[0]: row[1] for row in cursor.fetchall()}
            return {
                "knowledge_count": knowledge_count,
                "entity_count": entity_count,
                "categories": categories
            }
