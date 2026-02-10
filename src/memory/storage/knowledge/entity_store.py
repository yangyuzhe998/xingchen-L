import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
from src.utils.logger import logger

class EntityStoreMixin:
    """
    知识库实体与别名管理 Mixin
    """
    def add_entity(self, name: str, entity_type: str = "general",
                   aliases: List[str] = None, description: str = None) -> int:
        """
        添加实体 (支持别名自动更新)
        """
        now = datetime.now().isoformat()
        with self._get_conn() as conn:
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
                self.add_entity_alias(name, aliases or [])
                entity = self.get_entity_by_name(name)
                return entity.get('id', -1) if entity else -1

    def get_entity_by_name(self, name: str) -> Optional[Dict]:
        """通过名称获取实体"""
        with self._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM entities WHERE name = ?', (name,))
            row = cursor.fetchone()
            if row:
                result = dict(row)
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
        
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE entities SET aliases = ?, updated_at = ? WHERE name = ?
            ''', (json.dumps(updated_aliases, ensure_ascii=False), 
                  datetime.now().isoformat(), name))
            conn.commit()

    def resolve_alias(self, alias: str) -> Optional[str]:
        """解析别名返回标准名称"""
        with self._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT name FROM entities WHERE name = ?', (alias,))
            row = cursor.fetchone()
            if row:
                return row['name']
            
            cursor.execute('SELECT name, aliases FROM entities WHERE aliases IS NOT NULL')
            for row in cursor.fetchall():
                aliases = json.loads(row['aliases']) if row['aliases'] else []
                if alias in aliases:
                    return row['name']
            return None

    def get_all_entities(self, entity_type: str = None) -> List[Dict]:
        """获取所有实体"""
        with self._get_conn() as conn:
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
