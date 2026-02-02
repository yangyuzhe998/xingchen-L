from datetime import datetime
from typing import List, Dict
from ..models.entry import ShortTermMemoryEntry, LongTermMemoryEntry

class MemoryService:
    """
    记忆服务层
    整合 Vector, Json, Diary 存储，提供统一的记忆操作逻辑
    """
    def __init__(self, vector_storage, json_storage, diary_storage):
        self.vector_storage = vector_storage
        self.json_storage = json_storage
        self.diary_storage = diary_storage
        
        self.short_term: List[ShortTermMemoryEntry] = []
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
                self.long_term.append(LongTermMemoryEntry(content, category, created_at, meta))
            elif isinstance(item, str):
                # 旧格式纯字符串
                self.long_term.append(LongTermMemoryEntry(content=item))
        
        self.last_diary_time = datetime.now()

    def get_skill_collection(self):
        return self.vector_storage.get_skill_collection()

    def write_diary_entry(self, content):
        self.diary_storage.append(content)

    def add_short_term(self, role, content):
        entry = ShortTermMemoryEntry(role=role, content=content)
        self.short_term.append(entry)
        
        MAX_COUNT = 50
        if len(self.short_term) > MAX_COUNT:
            # 触发压缩逻辑 (外部控制或在此触发事件)
            pass

    def get_recent_history(self, limit=10):
        # 返回 dict 列表以兼容 LLM 接口
        return [entry.to_dict() for entry in self.short_term[-limit:]]

    def get_relevant_long_term(self, query=None, limit=5, search_mode="keyword"):
        """
        检索长期记忆
        :param query: 检索关键词
        :param limit: 返回条数
        :param search_mode: "keyword" (精准) | "hybrid" (混合/S脑用)
        """
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
                     print(f"[Memory] Vector search failed: {e}")
        
        # 合并逻辑
        if search_mode == "hybrid":
             # 混合模式：优先关键词，补充向量联想，去重
             all_hits = list(dict.fromkeys(keyword_hits + vector_hits)) # 保持顺序去重
             results = all_hits
        else:
             # 默认模式：仅关键词
             results = keyword_hits

        # 兜底：如果没查到，返回最新的几条事实（避免空上下文）
        if not results and limit > 0:
             results = [e.content for e in self.long_term[-limit:]]
            
        return "\n".join(results[:limit])

    def add_long_term(self, content, category="fact"):
        entry = LongTermMemoryEntry(content=content, category=category)
        self.long_term.append(entry)
        
        # 保存时转为 dict
        data_to_save = [e.to_dict() for e in self.long_term]
        self.json_storage.save(data_to_save)
        
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
                print(f"[Memory] 向量存储失败: {e}")
