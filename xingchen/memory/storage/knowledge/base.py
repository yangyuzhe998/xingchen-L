import sqlite3
import os
import json
from xingchen.config.settings import settings
from xingchen.utils.logger import logger

class KnowledgeBase:
    """
    知识库基础 Mixin: 负责数据库连接管理与表结构初始化
    """
    def _initialize_db(self):
        if not getattr(self, "db_path", None):
            self.db_path = settings.KNOWLEDGE_DB_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db_schema()

    def _init_db(self):
        """Backward-compatible alias for tests/legacy call sites."""
        self._initialize_db()

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
            
            conn.commit()
        logger.info(f"[KnowledgeBase] 数据库表结构初始化成功: {self.db_path}")

    def get_stats(self):
        """获取数据库统计信息 (Production Monitoring)"""
        stats = {}
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT count(*) FROM entities")
                stats["entities"] = cursor.fetchone()[0]
                cursor.execute("SELECT count(*) FROM knowledge")
                stats["knowledge"] = cursor.fetchone()[0]
                cursor.execute("SELECT count(*) FROM nodes")
                stats["nodes"] = cursor.fetchone()[0]
                cursor.execute("SELECT count(*) FROM edges")
                stats["edges"] = cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"[KnowledgeBase] 获取统计信息失败: {e}")
        return stats
