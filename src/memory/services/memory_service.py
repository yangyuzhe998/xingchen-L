import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from src.memory.models.entry import ShortTermMemoryEntry, LongTermMemoryEntry
from src.config.settings.settings import settings
from src.utils.logger import logger

class MemoryService:
    """
    记忆服务层
    整合 Vector, Json, Diary 存储，提供统一的记忆操作逻辑
    """
    def __init__(self, vector_storage, json_storage, diary_storage, knowledge_db=None):
        self.vector_storage = vector_storage
        self.json_storage = json_storage
        self.diary_storage = diary_storage
        # KnowledgeDB 是单例模式，因此我们可以使用传递的实例或创建一个新的实例
        # 但为了依赖注入 (便于测试)，我们保留这个参数
        from src.memory.storage.knowledge_db import KnowledgeDB
        self.knowledge_db = knowledge_db or KnowledgeDB() 

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
                meta = json.loads(item.get("meta", "{}")) if item.get("meta") else {}
                self.long_term.append(LongTermMemoryEntry(
                    content=item.get("content", ""),
                    category=item.get("category", "fact"),
                    created_at=item.get("created_at", datetime.now().isoformat()),
                    metadata=meta,
                    emotional_tag=meta.get("emotional_tag", {})  # 恢复情感标签
                ))
            logger.info(f"[Memory] 从 KnowledgeDB 加载了 {len(self.long_term)} 条长期记忆。")
        except Exception as e:
            logger.error(f"[Memory] 从 KnowledgeDB 加载失败: {e}")
            # 降级：如果 DB 出错，尝试从 JsonStorage 加载作为备份
            raw_long_term = self.json_storage.load()
            for item in raw_long_term:
                if isinstance(item, dict):
                    self.long_term.append(LongTermMemoryEntry(
                        content=item.get("content", ""),
                        category=item.get("category", "fact")
                    ))
        
        self.last_diary_time = datetime.now()

        # Alias cache for fast substring matching
        # alias -> target_name
        self._alias_cache: Dict[str, str] = {}
        self._load_alias_cache()

    def _load_alias_cache(self):
        """一次性加载所有别名到内存缓存中。"""
        try:
            all_entities = self.knowledge_db.get_all_entities()
            for entity in all_entities:
                name = entity['name']
                # 实体名本身也可以作为自己的别名
                self._alias_cache[name] = name
                aliases = entity.get('aliases', []) or []
                for alias in aliases:
                    if alias:
                        self._alias_cache[alias.strip()] = name
            logger.info(f"[Memory] 别名缓存加载完成，共 {len(self._alias_cache)} 条记录。")
        except Exception as e:
            logger.warning(f"[Memory] 别名缓存加载失败: {e}")

    def get_skill_collection(self):
        """获取技能集合"""
        return self.vector_storage.get_skill_collection()

    def get_command_docs_collection(self):
        """获取命令文档集合"""
        return self.vector_storage.get_command_docs_collection()

    def get_command_cases_collection(self):
        """获取命令案例集合"""
        return self.vector_storage.get_command_cases_collection()

    def get_alias_collection(self):
        return self.vector_storage.get_alias_collection()

    # [Phase 7 Refactor] Removed redundant property setter/getter
    # self.knowledge_db is now a direct public attribute logic
    
    def save_alias(self, alias, target_entity):
        """
        保存别名映射 (KnowledgeDB Implementation)
        :param alias: 别名 (e.g. "仔仔")
        :param target_entity: 目标实体 (e.g. "User")
        """
        # 标准化别名 (去重首尾空格)
        alias = alias.strip()
        if not alias: return

        try:
            # 直接调用 KnowledgeDB 的实体别名管理功能
            # 注意：如果 target_entity 不存在，会自动创建
            self.knowledge_db.add_entity(target_entity, entity_type="person") # 确保实体存在
            self.knowledge_db.add_entity_alias(target_entity, [alias])
            
            # 更新缓存
            self._alias_cache[alias] = target_entity
            logger.info(f"[Memory] 别名已更新 (KnowledgeDB): {alias} -> {target_entity}")
        except Exception as e:
            logger.error(f"[Memory] 别名存储失败: {e}", exc_info=True)

    def search_alias(self, query, limit=None, threshold=None):
        """
        检索别名（缓存实现）
        :param query: 用户输入的句子 (e.g. "仔仔饿了")
        :return: (alias, target_entity, score) or None
        """
        if limit is None:
            limit = settings.DEFAULT_ALIAS_LIMIT

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

    def write_diary_entry(self, content):
        """写入日记"""
        self.diary_storage.append(content)
        # 更新上次日记时间，使时间感知逻辑生效
        self.last_diary_time = datetime.now()

    def add_short_term(self, role, content):
        """添加短期记忆"""
        entry = ShortTermMemoryEntry(role=role, content=content)
        self.short_term.append(entry)
        self._short_term_dirty = True # 标记为脏数据
        
        if len(self.short_term) > settings.SHORT_TERM_MAX_COUNT:
            self.short_term.pop(0)
    
    def clear_short_term(self):
        """清空短期记忆缓存 (通常在压缩后调用)"""
        self.short_term = []
        self._short_term_dirty = True
        self.save_cache()

    def get_recent_history(self, limit=None):
        if limit is None: limit = settings.DEFAULT_SHORT_TERM_LIMIT
        # 返回 dict 列表以兼容 LLM 接口
        return [entry.to_dict() for entry in self.short_term[-limit:]]

    def get_relevant_long_term(self, query=None, limit=None, search_mode="keyword"):
        """
        检索长期记忆
        :param query: 检索关键词
        :param limit: 返回条数
        :param search_mode: "keyword" (精准) | "hybrid" (混合/S脑用)
        """
        if limit is None: limit = settings.DEFAULT_LONG_TERM_LIMIT
        
        # 1. 执行检索逻辑并获取匹配的对象条目 (Helper Logic)
        matched_entries: List[LongTermMemoryEntry] = []
        
        # 关键词匹配逻辑
        if query:
            query_lower = query.lower()
            for entry in self.long_term:
                if query_lower in entry.content.lower():
                    matched_entries.append(entry)
        
        # 2. [Phase 3.3] 触景生情：提取情感标签并产生轻微影响
        from src.psyche import psyche_engine
        emotional_impact = {}
        for entry in matched_entries[:limit]:
            if hasattr(entry, 'emotional_tag') and entry.emotional_tag:
                for emo, val in entry.emotional_tag.items():
                    # 以 0.1 的弱化系数影响当前情绪
                    emotional_impact[emo] = emotional_impact.get(emo, 0) + float(val) * 0.1
        
        if emotional_impact:
            psyche_engine.apply_emotion(emotional_impact)
            logger.debug(f"[Memory] 触景生情：检索触发情绪反馈 {emotional_impact}")

        # 3. 构造返回文本 (保持原有兼容性)
        results = [e.content for e in matched_entries[:limit]]

        # 4. 向量检索 (S脑增强 - 保持原有逻辑)
        if search_mode == "hybrid" and query:
             collection = self.vector_storage.get_memory_collection()
             if collection:
                 try:
                     search_res = collection.query(query_texts=[query], n_results=limit)
                     if search_res and search_res['documents']:
                         vector_docs = search_res['documents'][0]
                         results = list(dict.fromkeys(results + vector_docs))
                 except Exception as e:
                     logger.warning(f"[Memory] Vector search failed: {e}")
       
        # 5. 图谱检索 (保持原有逻辑)
        graph_context = []
        if search_mode == "hybrid" and query:
            try:
                found_nodes = self.knowledge_db.find_nodes_in_text(query)
                seen_nodes = set(found_nodes)
                for node in found_nodes:
                    related = self.knowledge_db.get_related_nodes(node, limit=3)
                    for rel in related:
                        if rel['neighbor'] not in seen_nodes:
                            graph_context.append(f"Knowledge: {node} --[{rel['relation']}]--> {rel['neighbor']}")
                            seen_nodes.add(rel['neighbor'])
            except Exception as e:
                logger.warning(f"[Memory] Graph search failed: {e}")

        if search_mode == "hybrid" and graph_context:
            results.append("\n--- Related Knowledge (Graph) ---")
            results.extend(graph_context)

        # 兜底：如果没查到，返回最新的几条事实
        if not results and limit > 0:
             results = [e.content for e in self.long_term[-limit:]]
            
        return "\n".join(results[:limit])

    def add_long_term(self, content, category="fact"):
        """
        添加长期记忆 (统一写入路径，支持双库幂等)
        [Phase 3] 自动附带当前情绪快照
        """
        import hashlib
        from src.psyche import psyche_engine

        # 抓取当前即时情绪作为标签
        current_emotions = {
            k: v["value"] for k, v in psyche_engine.get_raw_state().get("emotions", {}).items()
        }

        memory_id = hashlib.md5(f"{category}::{content}".encode()).hexdigest()
        entry = LongTermMemoryEntry(
            content=content, 
            category=category,
            emotional_tag=current_emotions
        )
        
        # 合并元数据
        meta_to_save = {
            "emotional_tag": current_emotions,
            "source": "user_interaction"
        }

        # 1. 存入 KnowledgeDB (权威真相源，支持 md5 幂等)
        try:
            db_id = self.knowledge_db.add_knowledge(
                content=content, 
                category=category,
                source="user_interaction",
                meta=json.dumps(meta_to_save, ensure_ascii=False)
            )
        except Exception as e:
            logger.error(f"[Memory] KnowledgeDB 写入失败: {e}", exc_info=True)

        # 2. 存入向量库 (语义索引，使用 memory_id 作为唯一 ID 实现幂等)
        collection = self.vector_storage.get_memory_collection()
        if collection:
            try:
                # 使用 memory_id 确保 ChromaDB 不会重复存储相同内容的向量
                collection.upsert(
                    documents=[content],
                    metadatas=[{
                        "category": category, 
                        "timestamp": entry.created_at,
                        "emotional_tag": json.dumps(current_emotions)
                    }],
                    ids=[f"mem_{memory_id}"]
                )
            except Exception as e:
                logger.error(f"[Memory] 向量存储失败: {e}", exc_info=True)
        
        # 3. 更新内存列表 (仅保留引用，标记为脏)
        self.long_term.append(entry)
        self._long_term_dirty = True

    def _load_cache(self) -> List[ShortTermMemoryEntry]:
        """加载短期记忆缓存"""
        path = settings.SHORT_TERM_CACHE_PATH
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                # 转换回对象
                # 注意：ShortTermMemoryEntry 的字段名必须与 dict key 匹配
                return [ShortTermMemoryEntry(**item) for item in data]
            except Exception as e:
                logger.error(f"[Memory] Failed to load cache: {e}", exc_info=True)
                return []
        return []

    def save_cache(self):
        """保存短期记忆缓存"""
        if not self._short_term_dirty:
            return

        path = settings.SHORT_TERM_CACHE_PATH
        data = [entry.to_dict() for entry in self.short_term]
        if not data:
            # 如果没有数据，删除缓存文件（如果存在）
            if os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass
            self._short_term_dirty = False
            return 
            
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            # logger.debug(f"[Memory] 短期记忆已缓存至: {path}")
            self._short_term_dirty = False
        except Exception as e:
            logger.error(f"[Memory] Failed to save cache: {e}", exc_info=True)

    def commit_long_term(self):
        """
        提交长期记忆
        
        当前长期记忆的权威真相源是 KnowledgeDB；但为了兼容现有组件与测试，
        这里仍然会将内存中的 long_term 镜像写入 JsonStorage。
        """
        if not self._long_term_dirty:
            return

        try:
            os.makedirs(os.path.dirname(self.json_storage.file_path), exist_ok=True)
            data = [e.to_dict() for e in self.long_term]
            self.json_storage.save(data)
            self._long_term_dirty = False
        except Exception as e:
            logger.error(f"[Memory] commit_long_term failed: {e}", exc_info=True)

    def commit_short_term(self):
        """
        提交短期记忆缓存
        """
        self.save_cache()

    def force_save_all(self):
        """
        强制持久化所有内存数据 (Intelligent Commit)
        包括: Graph, JsonStorage (LongTerm), ShortTermCache, AliasMap
        """
        # 1. 保存图谱 (由 GraphMemory 自己的 dirty flag 控制)
        # 需在 Memory Facade 中调用

        # 2. 保存长期记忆
        self.commit_long_term()

        # 3. 保存短期缓存
        self.commit_short_term()
        
        # 4. 别名映射是即时的
