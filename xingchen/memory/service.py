import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from xingchen.memory.models import ShortTermMemoryEntry, LongTermMemoryEntry
from xingchen.config.settings import settings
from xingchen.utils.logger import logger

class MemoryService:
    """
    记忆服务层
    整合 Vector, Json, Diary 存储，提供统一的记忆操作逻辑
    """
    def __init__(self, vector_storage, json_storage, diary_storage, knowledge_db=None):
        self.vector_storage = vector_storage
        self.json_storage = json_storage
        self.diary_storage = diary_storage
        from xingchen.memory.storage.knowledge_db import knowledge_db as kdb
        self.knowledge_db = knowledge_db or kdb

        # 优先加载缓存的未归档记忆，然后是空的列表
        self.short_term: List[ShortTermMemoryEntry] = self._load_cache()
        if self.short_term:
            logger.info(f"[Memory] 已恢复 {len(self.short_term)} 条未归档记忆。")

        # Dirty Flags for Service-managed data
        self._long_term_dirty = False
        self._short_term_dirty = False

        # 1. 优先从 KnowledgeDB 加载长期记忆 (作为新的真相源)
        self.long_term = []
        try:
            db_knowledge = self.knowledge_db.get_knowledge(limit=1000)
            for item in db_knowledge:
                meta = item.get("meta") or {}
                if isinstance(meta, str):
                    try:
                        meta = json.loads(meta)
                    except:
                        meta = {}
                self.long_term.append(LongTermMemoryEntry(
                    content=item.get("content", ""),
                    category=item.get("category", "fact"),
                    created_at=item.get("created_at", datetime.now().isoformat()),
                    metadata=meta,
                    emotional_tag=meta.get("emotional_tag", {})
                ))
            logger.info(f"[Memory] 从 KnowledgeDB 加载了 {len(self.long_term)} 条长期记忆。")
        except Exception as e:
            logger.error(f"[Memory] 从 KnowledgeDB 加载失败: {e}")
            raw_long_term = self.json_storage.load()
            for item in raw_long_term:
                if isinstance(item, dict):
                    self.long_term.append(LongTermMemoryEntry(
                        content=item.get("content", ""),
                        category=item.get("category", "fact")
                    ))
        
        self.last_diary_time = datetime.now()

        # Alias cache for fast substring matching
        self._alias_cache: Dict[str, str] = {}
        self._load_alias_cache()

    def _load_alias_cache(self):
        """一次性加载所有别名到内存缓存中。"""
        try:
            all_entities = self.knowledge_db.get_all_entities()
            for entity in all_entities:
                name = entity['name']
                self._alias_cache[name] = name
                aliases = entity.get('aliases', []) or []
                for alias in aliases:
                    if alias:
                        self._alias_cache[alias.strip()] = name
            logger.info(f"[Memory] 别名缓存加载完成，共 {len(self._alias_cache)} 条记录。")
        except Exception as e:
            logger.warning(f"[Memory] 别名缓存加载失败: {e}")

    def get_skill_collection(self):
        return self.vector_storage.get_skill_collection()

    def get_command_docs_collection(self):
        return self.vector_storage.get_command_docs_collection()

    def get_command_cases_collection(self):
        return self.vector_storage.get_command_cases_collection()

    def get_alias_collection(self):
        return self.vector_storage.get_alias_collection()

    def save_alias(self, alias, target_entity):
        alias = alias.strip()
        if not alias: return

        try:
            self.knowledge_db.add_entity(target_entity, entity_type="person")
            self.knowledge_db.add_entity_alias(target_entity, [alias])
            self._alias_cache[alias] = target_entity
            logger.info(f"[Memory] 别名已更新 (KnowledgeDB): {alias} -> {target_entity}")
        except Exception as e:
            logger.error(f"[Memory] 别名存储失败: {e}", exc_info=True)

    def search_alias(self, query, limit=None):
        if not query:
            return None

        try:
            matches = []
            for alias, target in self._alias_cache.items():
                if alias and alias in query:
                    matches.append((alias, target, len(alias)))

            if matches:
                matches.sort(key=lambda x: x[2], reverse=True)
                best = matches[0]
                return (best[0], best[1], 1.0)
        except Exception as e:
            logger.warning(f"[Memory] 别名检索失败: {e}")

        return None

    def search_long_term(self, query: str, limit: int = 5) -> List[LongTermMemoryEntry]:
        """
        搜索长期记忆 (结合知识库搜索与向量搜索)
        """
        # 1. 知识库搜索
        results = self.knowledge_db.search_knowledge(query, limit=limit)
        
        entries = []
        for item in results:
            meta = item.get("meta") or {}
            if isinstance(meta, str):
                try:
                    meta = json.loads(meta)
                except:
                    meta = {}
            entries.append(LongTermMemoryEntry(
                content=item.get("content", ""),
                category=item.get("category", "fact"),
                created_at=item.get("created_at", datetime.now().isoformat()),
                metadata=meta,
                emotional_tag=meta.get("emotional_tag", {})
            ))
            
        # 2. 如果结果不足，补充向量搜索 (TODO)
        
        return entries

    def write_diary_entry(self, content):
        self.diary_storage.append(content)
        self.last_diary_time = datetime.now()

    def add_short_term(self, role, content):
        entry = ShortTermMemoryEntry(role=role, content=content)
        self.short_term.append(entry)
        self._short_term_dirty = True
        
        if len(self.short_term) > settings.SHORT_TERM_MAX_COUNT:
            self.short_term.pop(0)
    
    def clear_short_term(self):
        self.short_term = []
        self._short_term_dirty = True
        self.save_cache()

    def get_recent_history(self, limit=None):
        if limit is None: limit = settings.DEFAULT_SHORT_TERM_LIMIT
        return [entry.to_dict() for entry in self.short_term[-limit:]]

    def get_relevant_long_term(self, query=None, limit=None, search_mode="keyword"):
        if limit is None: limit = settings.DEFAULT_LONG_TERM_LIMIT
        
        matched_entries: List[LongTermMemoryEntry] = []
        
        if query:
            query_lower = query.lower()
            for entry in self.long_term:
                if query_lower in entry.content.lower():
                    matched_entries.append(entry)
        
        # 触景生情
        from xingchen.psyche import psyche_engine
        emotional_impact = {}
        for entry in matched_entries[:limit]:
            if hasattr(entry, 'emotional_tag') and entry.emotional_tag:
                for emo, val in entry.emotional_tag.items():
                    emotional_impact[emo] = emotional_impact.get(emo, 0) + float(val) * settings.EMOTIONAL_RESONANCE_FACTOR
        
        if emotional_impact:
            psyche_engine.apply_emotion(emotional_impact)
            logger.debug(f"[Memory] 触景生情：检索触发情绪反馈 {emotional_impact}")

        return [e.content for e in matched_entries[:limit]]

    def add_long_term(self, content, category="fact", meta=None, emotional_tag=None):
        if not content: return
        
        # 写入 KnowledgeDB (持久化源)
        try:
            self.knowledge_db.add_knowledge(
                content=content,
                category=category,
                meta=meta
            )
        except Exception as e:
            logger.error(f"[Memory] 写入 KnowledgeDB 失败: {e}")

        # 更新内存缓存
        entry = LongTermMemoryEntry(
            content=content, 
            category=category,
            metadata=meta or {},
            emotional_tag=emotional_tag or {}
        )
        self.long_term.append(entry)
        self._long_term_dirty = True
        
        # 异步推送到向量数据库 (TODO)
        return entry

    def save_cache(self):
        if self._short_term_dirty:
            self._save_cache(self.short_term)
            self._short_term_dirty = False
            
        if self._long_term_dirty:
            # 长期记忆现在由 KnowledgeDB 持久化，这里的 json 仅作备份或兼容
            self.json_storage.save([e.to_dict() for e in self.long_term])
            self._long_term_dirty = False

    def _load_cache(self) -> List[ShortTermMemoryEntry]:
        path = settings.SHORT_TERM_CACHE_PATH
        if not os.path.exists(path):
            return []
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [ShortTermMemoryEntry.from_dict(d) for d in data]
        except Exception as e:
            logger.error(f"[Memory] 加载短期记忆缓存失败: {e}")
            return []

    def _save_cache(self, entries: List[ShortTermMemoryEntry]):
        path = settings.SHORT_TERM_CACHE_PATH
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump([e.to_dict() for e in entries], f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"[Memory] 保存短期记忆缓存失败: {e}")
