import json
import sqlite3
from datetime import datetime
from typing import List, Dict
from src.utils.logger import logger

class KnowledgeStoreMixin:
    """
    知识库事实存取 Mixin
    """
    def add_knowledge(self, content: str, category: str = "fact", 
                      source: str = None, confidence: float = 1.0,
                      meta: Dict = None) -> int:
        """
        添加一条知识 (支持内容哈希去重幂等)
        """
        import hashlib
        content_hash = hashlib.md5(f"{category}::{content}".encode()).hexdigest()
        now = datetime.now().isoformat()
        
        with self._get_conn() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO knowledge (content_hash, content, category, source, confidence, verified_at, created_at, meta)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (content_hash, content, category, source, confidence, now, now, 
                      json.dumps(meta, ensure_ascii=False) if meta else None))
                conn.commit()
                knowledge_id = cursor.lastrowid
                logger.info(f"[KnowledgeDB] Added knowledge #{knowledge_id}: {content[:50]}...")
                return knowledge_id
            except sqlite3.IntegrityError:
                # 幂等处理
                cursor.execute('''
                    UPDATE knowledge SET 
                        confidence = MAX(confidence, ?),
                        verified_at = ?
                    WHERE content_hash = ?
                ''', (confidence, now, content_hash))
                conn.commit()
                cursor.execute('SELECT id FROM knowledge WHERE content_hash = ?', (content_hash,))
                row = cursor.fetchone()
                return row[0] if row else -1

    def get_knowledge(self, category: str = None, limit: int = 100) -> List[Dict]:
        """
        获取知识列表
        """
        with self._get_conn() as conn:
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
            results = []
            for row in rows:
                item = dict(row)
                if item.get("meta"):
                    try:
                        item["meta"] = json.loads(item["meta"])
                    except:
                        item["meta"] = {}
                else:
                    item["meta"] = {}
                results.append(item)
            return results

    def search_knowledge(self, query: str, limit: int = 10) -> List[Dict]:
        """
        搜索知识 (精确匹配)
        """
        with self._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM knowledge 
                WHERE content LIKE ? 
                ORDER BY confidence DESC, created_at DESC 
                LIMIT ?
            ''', (f'%{query}%', limit))
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                item = dict(row)
                if item.get("meta"):
                    try:
                        item["meta"] = json.loads(item["meta"])
                    except:
                        item["meta"] = {}
                else:
                    item["meta"] = {}
                results.append(item)
            
            logger.debug(f"[KnowledgeDB] Search '{query}' returned {len(results)} results")
            return results

    def update_knowledge_confidence(self, knowledge_id: int, confidence: float):
        """更新知识置信度"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE knowledge SET confidence = ?, verified_at = ? WHERE id = ?
            ''', (confidence, datetime.now().isoformat(), knowledge_id))
            conn.commit()
            logger.debug(f"[KnowledgeDB] Updated knowledge #{knowledge_id} confidence to {confidence}")

    def delete_knowledge(self, knowledge_id: int):
        """删除知识"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM knowledge WHERE id = ?', (knowledge_id,))
            conn.commit()
            return cursor.rowcount > 0
