"""
知识库存储模块 (Knowledge Database)
基于 SQLite 实现知识和实体的持久化存储

表结构:
- knowledge: 存储验证过的事实/知识
- entities: 存储实体及其别名
"""
import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Any
from src.utils.logger import logger
from src.config.settings.settings import settings


class KnowledgeDB:
    """
    知识库 (Knowledge Database)
    用于存储验证过的知识和实体信息
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(KnowledgeDB, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        self.db_path = os.path.join(settings.MEMORY_DATA_DIR, "knowledge.db")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()
        self._initialized = True
        
    def _get_conn(self):
        """获取数据库连接 (Context Manager)"""
        return sqlite3.connect(self.db_path)
        
    def _init_db(self):
        """初始化数据库表结构 (自动迁移)"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            
            # [迁移检查] 检查 entities 表是否包含 'subject' 列 (Phase 7 错误)
            # 如果存在，说明是错误的 Schema，需要删除重建以恢复到 Phase 1 (name, aliases...)
            cursor.execute("PRAGMA table_info(entities)")
            columns = [info[1] for info in cursor.fetchall()]
            if 'subject' in columns:
                logger.warning("[KnowledgeDB] 检测到错误的三元组 Schema (Phase 7 Deprecated). 正在重置 entities 表...")
                cursor.execute("DROP TABLE IF EXISTS entities")
                # knowledge 表通常不受影响，为了安全起见保留
            
            # 1. 实体表 (Entity - Named Object, Legacy Phase 1)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS entities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    entity_type TEXT DEFAULT 'general',
                    aliases TEXT,          -- JSON List
                    description TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 1.5 知识表 (Knowledge - Unstructured/Semi-structured Text)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS knowledge (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    category TEXT DEFAULT 'fact',
                    source TEXT,
                    confidence FLOAT DEFAULT 1.0,
                    verified_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    meta TEXT
                )
            ''')
            
            # 2. 从句表 (Clause) - 用于逻辑推理
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS clauses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    expression TEXT NOT NULL,  -- 逻辑表达式 e.g. "rain -> wet"
                    type TEXT DEFAULT 'rule',  -- rule/fact
                    weight FLOAT DEFAULT 1.0,  -- 权重
                    meta TEXT                  -- 元数据 JSON
                )
            ''')
            
            # [Phase 7] 3. 图节点表 (Graph Nodes)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS nodes (
                    name TEXT PRIMARY KEY,
                    type TEXT DEFAULT 'concept', -- concept, entity, event
                    weight FLOAT DEFAULT 1.0,    -- 节点重要性 (PageRank-like)
                    meta TEXT,                   -- 元数据 JSON
                    last_activated DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # [Phase 7] 4. 图边表 (Graph Edges)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS edges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    target TEXT NOT NULL,
                    relation TEXT DEFAULT 'RELATED_TO', -- RELATED_TO, CAUSED_BY, HAS_A
                    weight FLOAT DEFAULT 1.0,           -- 关联强度
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(source) REFERENCES nodes(name),
                    FOREIGN KEY(target) REFERENCES nodes(name),
                    UNIQUE(source, target, relation)
                )
            ''')
            
            # 索引优化
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_edge_source ON edges(source)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_edge_target ON edges(target)')
            
            conn.commit()
            logger.info(f"[KnowledgeDB] Database initialized at {self.db_path}")
    
    # ============ Knowledge CRUD (知识增删改查) ============
    
    def add_knowledge(self, content: str, category: str = "fact", 
                      source: str = None, confidence: float = 1.0,
                      meta: Dict = None) -> int:
        """
        添加一条知识
        :param content: 知识内容
        :param category: 分类 (fact, rule, preference)
        :param source: 来源 (web_search, user_input, s_brain)
        :param confidence: 置信度 (0.0-1.0)
        :param meta: 元数据
        :return: 知识 ID
        """
        now = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO knowledge (content, category, source, confidence, verified_at, created_at, meta)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (content, category, source, confidence, now, now, 
                  json.dumps(meta, ensure_ascii=False) if meta else None))
            conn.commit()
            knowledge_id = cursor.lastrowid
            logger.info(f"[KnowledgeDB] Added knowledge #{knowledge_id}: {content[:50]}...")
            return knowledge_id
    
    def get_knowledge(self, category: str = None, limit: int = 100) -> List[Dict]:
        """
        获取知识列表
        :param category: 按分类过滤
        :param limit: 返回数量上限
        :return: 知识列表
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if category:
                cursor.execute('''
                    SELECT * FROM knowledge WHERE category = ? 
                    ORDER BY created_at DESC LIMIT ?
                ''', (category, limit))
            else:
                cursor.execute('''
                    SELECT * FROM knowledge ORDER BY created_at DESC LIMIT ?
                ''', (limit,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def search_knowledge(self, query: str, limit: int = 10) -> List[Dict]:
        """
        搜索知识 (精确匹配)
        :param query: 搜索关键词
        :param limit: 返回数量上限
        :return: 匹配的知识列表
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM knowledge 
                WHERE content LIKE ? 
                ORDER BY confidence DESC, created_at DESC 
                LIMIT ?
            ''', (f'%{query}%', limit))
            rows = cursor.fetchall()
            logger.debug(f"[KnowledgeDB] Search '{query}' returned {len(rows)} results")
            return [dict(row) for row in rows]
    
    def update_knowledge_confidence(self, knowledge_id: int, confidence: float):
        """更新知识置信度"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE knowledge SET confidence = ?, verified_at = ? WHERE id = ?
            ''', (confidence, datetime.now().isoformat(), knowledge_id))
            conn.commit()
            logger.debug(f"[KnowledgeDB] Updated knowledge #{knowledge_id} confidence to {confidence}")
    
    def delete_knowledge(self, knowledge_id: int):
        """删除知识"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM knowledge WHERE id = ?', (knowledge_id,))
            conn.commit()
            return cursor.rowcount > 0

    # -------------------------------------------------------------------------
    # Graph Operations (图谱操作 - Phase 7)
    # -------------------------------------------------------------------------

    def add_node(self, name: str, type: str = "concept", weight: float = 1.0, meta: Dict = None):
        """
        添加或更新图节点
        """
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

    def add_edge(self, source: str, target: str, relation: str = "RELATED_TO", weight: float = 1.0):
        """
        添加或更新边 (自动创建缺失的节点)
        """
        # 确保节点存在
        self.add_node(source)
        self.add_node(target)
        
        with self._get_conn() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO edges (source, target, relation, weight, created_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(source, target, relation) DO UPDATE SET
                        weight = excluded.weight
                ''', (source, target, relation, weight))
                conn.commit()
                return True
            except Exception as e:
                logger.error(f"[KnowledgeDB] Failed to add edge {source}->{target}: {e}")
                return False

    def get_related_nodes(self, node_name: str, min_weight: float = 0.5, limit: int = 10) -> List[Dict]:
        """
        获取相关联的节点 (Graph Traversal Step 1)
        """
        with self._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 查找出边和入边
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
        """
        从文本中查找已知的节点 (Entity Linking 简单实现)
        :param text: 输入文本
        :return: 匹配到的节点名称列表
        """
        if not text: return []
        
        with self._get_conn() as conn:
            cursor = conn.cursor()
            # 查找所有节点名称，如果在文本中出现
            # 注意: 为了性能，这里应该用 FTS (全文检索) 或者 Aho-Corasick 算法
            # 但 SQLite 简单起见，我们只能反向 LIKE 或者加载所有节点到内存匹配 (如果不大的话)
            # 方案: SELECT name FROM nodes WHERE instr(?, name) > 0
            # 限制: name 太短可能会错误匹配 (e.g. "a") -> 可以在 SQL 中过滤 length(name) > 1
            
            cursor.execute('''
                SELECT name FROM nodes 
                WHERE LENGTH(name) > 1 AND instr(?, name) > 0
                ORDER BY length(name) DESC
                LIMIT 5
            ''', (text,))
            
            rows = cursor.fetchall()
            return [row[0] for row in rows]
    
    # ============ Entity CRUD (实体增删改查) ============
    
    def add_entity(self, name: str, entity_type: str = "general",
                   aliases: List[str] = None, description: str = None) -> int:
        """
        添加实体
        :param name: 实体名称 (唯一)
        :param entity_type: 实体类型 (person, concept, project)
        :param aliases: 别名列表
        :param description: 描述
        :return: 实体 ID
        """
        now = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO entities (name, entity_type, aliases, description, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (name, entity_type, 
                      json.dumps(aliases, ensure_ascii=False) if aliases else None,
                      description, now, now))
                conn.commit()
                entity_id = cursor.lastrowid
                logger.info(f"[KnowledgeDB] Added entity #{entity_id}: {name}")
                return entity_id
            except sqlite3.IntegrityError:
                # 实体已存在，更新别名
                logger.info(f"[KnowledgeDB] Entity {name} already exists, updating aliases")
                self.add_entity_alias(name, aliases or [])
                return self.get_entity_by_name(name).get('id', -1)
    
    def get_entity_by_name(self, name: str) -> Optional[Dict]:
        """通过名称获取实体"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM entities WHERE name = ?', (name,))
            row = cursor.fetchone()
            if row:
                result = dict(row)
                # 解析 aliases JSON
                if result.get('aliases'):
                    result['aliases'] = json.loads(result['aliases'])
                return result
            return None
    
    def add_entity_alias(self, name: str, new_aliases: List[str]):
        """为实体添加别名"""
        entity = self.get_entity_by_name(name)
        if not entity:
            return
        
        current_aliases = entity.get('aliases', []) or []
        updated_aliases = list(set(current_aliases + new_aliases))
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE entities SET aliases = ?, updated_at = ? WHERE name = ?
            ''', (json.dumps(updated_aliases, ensure_ascii=False), 
                  datetime.now().isoformat(), name))
            conn.commit()
    
    def resolve_alias(self, alias: str) -> Optional[str]:
        """
        解析别名，返回标准实体名称
        :param alias: 别名
        :return: 标准名称，如果不存在返回 None
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 先精确匹配名称
            cursor.execute('SELECT name FROM entities WHERE name = ?', (alias,))
            row = cursor.fetchone()
            if row:
                return row['name']
            
            # 再搜索别名 (JSON 数组搜索)
            cursor.execute('SELECT name, aliases FROM entities WHERE aliases IS NOT NULL')
            for row in cursor.fetchall():
                aliases = json.loads(row['aliases']) if row['aliases'] else []
                if alias in aliases:
                    return row['name']
            
            return None
    
    def get_all_entities(self, entity_type: str = None) -> List[Dict]:
        """获取所有实体"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if entity_type:
                cursor.execute('SELECT * FROM entities WHERE entity_type = ?', (entity_type,))
            else:
                cursor.execute('SELECT * FROM entities')
            
            rows = cursor.fetchall()
            results = []
            for row in rows:
                result = dict(row)
                if result.get('aliases'):
                    result['aliases'] = json.loads(result['aliases'])
                results.append(result)
            return results
    
    # ============ 统计信息 ============
    
    def get_stats(self) -> Dict:
        """获取数据库统计信息"""
        with sqlite3.connect(self.db_path) as conn:
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


# 全局实例
knowledge_db = KnowledgeDB()
