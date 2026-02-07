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
        self._init_database()
        self._initialized = True
        
    def _init_database(self):
        """初始化数据库表结构"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 知识表: 存储验证过的事实
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS knowledge (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    category TEXT DEFAULT 'fact',
                    source TEXT,
                    confidence REAL DEFAULT 1.0,
                    verified_at TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    meta TEXT
                )
            ''')
            
            # 实体表: 存储实体及其别名
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS entities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    entity_type TEXT DEFAULT 'general',
                    aliases TEXT,
                    description TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_knowledge_category ON knowledge (category)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_knowledge_content ON knowledge (content)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_entities_name ON entities (name)')
            
            conn.commit()
            logger.info(f"[KnowledgeDB] Database initialized at {self.db_path}")
    
    # ============ Knowledge CRUD ============
    
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
            logger.debug(f"[KnowledgeDB] Deleted knowledge #{knowledge_id}")
    
    # ============ Entity CRUD ============
    
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
