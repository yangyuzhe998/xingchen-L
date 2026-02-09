import json
import os
from datetime import datetime
from typing import List, Dict
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

        # 加载时将 dict 转换为 LongTermMemoryEntry 对象 (如果需要)
        # 简单起见，这里假设 load 返回的是 dict 列表，我们暂时保持兼容，或者在 load 后转换
        raw_long_term = self.json_storage.load()
        self.long_term = []
        for item in raw_long_term:
            if isinstance(item, dict):
                # 尝试适配旧格式
                content = item.get("content", "")
                category = item.get("category", "fact")
                created_at = item.get("created_at", datetime.now().isoformat())
                meta = item.get("metadata", {})
                self.long_term.append(LongTermMemoryEntry(
                    content=content,
                    category=category,
                    created_at=created_at,
                    metadata=meta
                ))
            elif isinstance(item, str):
                # 旧格式纯字符串
                self.long_term.append(LongTermMemoryEntry(content=item))
        
        self.last_diary_time = datetime.now()

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
        保存别名映射 (JSON Implementation)
        :param alias: 别名 (e.g. "仔仔")
        :param target_entity: 目标实体 (e.g. "User")
        """
        try:
            path = settings.ALIAS_MAP_PATH
            data = {}
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError:
                        data = {}
            
            # 标准化别名 (去重首尾空格)
            alias = alias.strip()
            if not alias: return

            # 更新映射: alias -> {target, timestamp}
            data[alias] = {
                "target": target_entity,
                "timestamp": datetime.now().isoformat()
            }
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            logger.info(f"[Memory] 别名已更新 (JSON): {alias} -> {target_entity}")
        except Exception as e:
            logger.error(f"[Memory] 别名存储失败: {e}", exc_info=True)

    def search_alias(self, query, limit=None, threshold=None):
        """
        检索别名 (Substring Match Implementation)
        :param query: 用户输入的句子 (e.g. "仔仔饿了")
        :return: (alias, target_entity, score) or None
        """
        if limit is None: limit = settings.DEFAULT_ALIAS_LIMIT
        if threshold is None: threshold = settings.DEFAULT_ALIAS_THRESHOLD

        try:
            path = settings.ALIAS_MAP_PATH
            if not os.path.exists(path):
                return None
                
            with open(path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    return None
            
            # 查找 query 中是否包含任何已知的 alias
            # 优先匹配最长的 alias (防止 "小王" 匹配到 "小王子")
            matches = []
            for alias, info in data.items():
                if alias in query:
                    matches.append((alias, info['target'], len(alias)))
            
            if matches:
                # 按长度降序排序
                matches.sort(key=lambda x: x[2], reverse=True)
                best_match = matches[0]
                return (best_match[0], best_match[1], 1.0) # 完全子串匹配得分为 1.0
                
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
        results = []
        
        # 1. 关键词匹配 (基础)
        keyword_hits = []
        if query:
            query_lower = query.lower()
            for entry in self.long_term:
                content = entry.content
                if query_lower in content.lower():
                    keyword_hits.append(content)
        
        # 2. 向量检索 (S脑增强)
        vector_hits = []
        if search_mode == "hybrid" and query:
             collection = self.vector_storage.get_memory_collection()
             if collection:
                 try:
                     # 向量检索逻辑
                     search_res = collection.query(query_texts=[query], n_results=limit)
                     if search_res and search_res['documents']:
                         vector_hits = search_res['documents'][0]
                 except Exception as e:
                    logger.warning(f"[Memory] Vector search failed: {e}")
       
        # 3. 图谱检索 (Graph Search - Phase 7)
        graph_context = []
        if search_mode == "hybrid" and query:
            try:
                # A. 实体链接 (Entity Linking)
                found_nodes = self.knowledge_db.find_nodes_in_text(query)
                
                # B. 扩散激活 (Spreading Activation)
                seen_nodes = set(found_nodes)
                for node in found_nodes:
                    # 获取直接关联的节点 (1-hop)
                    related = self.knowledge_db.get_related_nodes(node, limit=3)
                    for rel in related:
                        neighbor = rel['neighbor']
                        relation = rel['relation']
                        if neighbor not in seen_nodes:
                            # 格式化为自然语言: "Python --[RELATED_TO]--> Spider"
                            graph_context.append(f"Knowledge: {node} --[{relation}]--> {neighbor}")
                            seen_nodes.add(neighbor)
            except Exception as e:
                logger.warning(f"[Memory] Graph search failed: {e}")

        # 合并逻辑
        if search_mode == "hybrid":
             # 混合模式：优先关键词，补充向量联想，去重，最后附带图谱上下文
             # 1. Memory Hits (Keyword + Vector)
             memory_hits = list(dict.fromkeys(keyword_hits + vector_hits))
             
             # 2. Results composition
             results = memory_hits
             
             # 3. Append Graph Context (if any)
             if graph_context:
                 results.append("\n--- Related Knowledge (Graph) ---")
                 results.extend(graph_context)
        else:
             # 默认模式：仅关键词
             results = keyword_hits

        # 兜底：如果没查到，返回最新的几条事实（避免空上下文）
        if not results and limit > 0:
             results = [e.content for e in self.long_term[-limit:]]
            
        return "\n".join(results[:limit])

    def add_long_term(self, content, category="fact"):
        """添加长期记忆"""
        entry = LongTermMemoryEntry(content=content, category=category)
        self.long_term.append(entry)
        self._long_term_dirty = True # 标记为脏数据
        
        # 同时保存到 JSON 文件
        # 移除每次 add 都全量保存的逻辑，改为由 dirty check 驱动的批量保存
        # self.json_storage.save(all_data)
        
        # 同时存入向量库
        collection = self.vector_storage.get_memory_collection()
        if collection:
            try:
                collection.add(
                    documents=[content],
                    metadatas=[{"category": category, "timestamp": entry.created_at}],
                    ids=[f"mem_{int(datetime.now().timestamp())}_{len(self.long_term)}"] # 增加索引防止极速写入冲突
                )
            except Exception as e:
                logger.error(f"[Memory] 向量存储失败: {e}", exc_info=True)

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
        提交长期记忆 (JSON)
        """
        if self._long_term_dirty:
            try:
                all_data = [e.to_dict() for e in self.long_term]
                self.json_storage.save(all_data)
                self._long_term_dirty = False
                logger.info("[Memory] 长期记忆 (JSON) 已提交。")
            except Exception as e:
                logger.error(f"[Memory] 长期记忆提交失败: {e}", exc_info=True)

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
