import json
import os
from datetime import datetime
import chromadb
from chromadb.utils import embedding_functions

class Memory:
    """
    记忆模块基础实现
    包含：
    1. 短期记忆 (ShortTerm): 最近的对话历史 (RAM)
    2. 长期记忆 (LongTerm): 重要的事实或规则 (Disk/JSON + ChromaDB Vector)
    """
    def __init__(self, storage_path="src/memory/storage.json", vector_db_path="src/memory/chroma_db"):
        self.short_term = []
        self.long_term = []
        self.storage_path = storage_path
        
        # 初始化 ChromaDB
        try:
            self.chroma_client = chromadb.PersistentClient(path=vector_db_path)
            # 使用默认的 embedding 模型 (sentence-transformers/all-MiniLM-L6-v2)
            # 注意：首次运行会自动下载模型
            self.collection = self.chroma_client.get_or_create_collection(
                name="long_term_memory",
                metadata={"hnsw:space": "cosine"}
            )
            print("[Memory] ChromaDB 向量数据库初始化成功。")
        except Exception as e:
            print(f"[Memory] ChromaDB 初始化失败: {e}")
            self.collection = None

        self._load_long_term()
        print("[Memory] 记忆系统初始化完成。")

    def add_short_term(self, role, content):
        """添加短期对话记忆 (带滑动窗口)"""
        self.short_term.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        # 滑动窗口策略 (Sliding Window):
        # 1. 数量限制 (MAX_COUNT): 防止条目过多
        # 2. 字符限制 (MAX_CHARS): 防止 Context Window 溢出 (估算 1 token ≈ 2-3 chars)
        
        MAX_COUNT = 50
        MAX_CHARS = 20000 
        
        # 1. 按数量裁剪
        while len(self.short_term) > MAX_COUNT:
            self.short_term.pop(0)
            
        # 2. 按字符数裁剪
        current_chars = sum(len(m['content']) for m in self.short_term)
        while current_chars > MAX_CHARS and len(self.short_term) > 2: # 至少保留最近一轮对话
            removed = self.short_term.pop(0)
            current_chars -= len(removed['content'])

    def add_long_term(self, content, category="fact"):
        """添加长期记忆 (同步写入 ChromaDB)"""
        timestamp = datetime.now().isoformat()
        entry = {
            "content": content,
            "category": category,
            "created_at": timestamp
        }
        self.long_term.append(entry)
        
        # 写入 JSON
        self._save_long_term()
        
        # 写入 ChromaDB
        if self.collection:
            try:
                # 使用 timestamp + hash 作为 ID，防止重复
                import hashlib
                entry_id = hashlib.md5((content + timestamp).encode()).hexdigest()
                
                self.collection.add(
                    documents=[content],
                    metadatas=[{"category": category, "timestamp": timestamp}],
                    ids=[entry_id]
                )
                print(f"[Memory] 向量索引已更新 (ID: {entry_id[:8]})")
            except Exception as e:
                print(f"[Memory] 向量写入失败: {e}")
                
        print(f"[Memory] 已固化长期记忆: {content[:20]}...")

    def get_recent_history(self, limit=5):
        """获取最近的对话历史 (用于 Prompt 上下文)"""
        return [{"role": m["role"], "content": m["content"]} for m in self.short_term[-limit:]]

    def get_relevant_long_term(self, query=None):
        """
        获取相关的长期记忆
        采用混合检索策略 (Hybrid Retrieval):
        1. 向量检索 (Semantic Search via ChromaDB): 捕捉语义相关性
        2. 关键词匹配 (Keyword Match): 捕捉精确词汇
        3. 最近记忆 (Recency): 补充上下文
        """
        if not self.long_term:
            return ""
        
        relevant_contents = set()
        
        # 1. 向量检索 (Semantic)
        if query and self.collection:
            try:
                results = self.collection.query(
                    query_texts=[query],
                    n_results=3 # 取语义最相关的前3条
                )
                if results['documents']:
                    for doc in results['documents'][0]:
                        relevant_contents.add(f"[Semantic] {doc}")
            except Exception as e:
                print(f"[Memory] 向量检索失败: {e}")

        # 2. 关键词检索 (Keyword - 简化版)
        if query:
            for entry in self.long_term:
                content = entry['content']
                # 简单匹配：query 中的词是否在 content 中
                if query in content: # 完整包含
                    relevant_contents.add(f"[Keyword] {content}")
                else:
                    # 分词匹配 (简单空格分割)
                    hits = 0
                    words = query.split()
                    for w in words:
                        if len(w) > 1 and w in content:
                            hits += 1
                    if hits > 0 and hits >= len(words) * 0.5: # 命中一半以上关键词
                        relevant_contents.add(f"[Keyword] {content}")

        # 3. 最近记忆 (Recency) - 始终补充最近的 3 条
        for entry in self.long_term[-3:]:
             # 避免重复 (去掉前缀比较)
             content = entry['content']
             is_duplicate = False
             for r in relevant_contents:
                 if content in r:
                     is_duplicate = True
                     break
             if not is_duplicate:
                 relevant_contents.add(f"[Recency] {content}")

        # 格式化输出
        if not relevant_contents:
            return ""
            
        summary = "长期记忆 (Long-Term Memory):\n"
        for content in relevant_contents:
            # 去掉我们自己加的前缀，或者保留以便 debug
            # 这里为了给 LLM 看，保留前缀有助于它理解记忆来源
            summary += f"- {content}\n"
        
        return summary

    def _load_long_term(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    self.long_term = json.load(f)
            except Exception as e:
                print(f"[Memory] 加载长期记忆失败: {e}")

    def _save_long_term(self):
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(self.long_term, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Memory] 保存长期记忆失败: {e}")
