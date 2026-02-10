import sqlite3
import os
import json
from src.config.settings.settings import settings
from src.utils.logger import logger

class KnowledgeBase:
    """
    知识库基础 Mixin: 负责数据库连接管理与表结构初始化
    """
    def _initialize_db(self):
        self.db_path = os.path.join(settings.MEMORY_DATA_DIR, "knowledge.db")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db_schema()

    def _get_conn(self):
        """获取数据库连接 (Context Manager)"""
        conn = sqlite3.connect(self.db_path, timeout=30)
        # 启用 WAL 模式提高并发性能
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db_schema(self):
        """初始化数据库表结构 (自动迁移)"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            
            # 1. 实体表
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

            # 1.5 知识表 (支持内容哈希去重幂等)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS knowledge (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content_hash TEXT UNIQUE, 
                    content TEXT NOT NULL,
                    category TEXT DEFAULT 'fact',
                    source TEXT,
                    confidence FLOAT DEFAULT 1.0,
                    verified_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    meta TEXT
                )
            ''')
            
            # 2. 从句表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS clauses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    expression TEXT NOT NULL UNIQUE,
                    type TEXT DEFAULT 'rule',  
                    weight FLOAT DEFAULT 1.0,  
                    meta TEXT                  
                )
            ''')
            
            # 3. 图节点表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS nodes (
                    name TEXT PRIMARY KEY,
                    type TEXT DEFAULT 'concept',
                    weight FLOAT DEFAULT 1.0,
                    meta TEXT,
                    last_activated DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 4. 图边表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS edges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    target TEXT NOT NULL,
                    relation TEXT DEFAULT 'RELATED_TO',
                    relation_type TEXT DEFAULT 'general',
                    weight FLOAT DEFAULT 1.0,
                    meta TEXT,
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
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_edge_relation_type ON edges(relation_type)')
            
            conn.commit()
            logger.info(f"[KnowledgeDB] Database initialized at {self.db_path}")
