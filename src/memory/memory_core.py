import json
import os
from datetime import datetime

class Memory:
    """
    记忆模块基础实现
    包含：
    1. 短期记忆 (ShortTerm): 最近的对话历史 (RAM)
    2. 长期记忆 (LongTerm): 重要的事实或规则 (Disk/JSON)
    """
    def __init__(self, storage_path="src/memory/storage.json"):
        self.short_term = []
        self.long_term = []
        self.storage_path = storage_path
        self._load_long_term()
        print("[Memory] 记忆系统初始化完成。")

    def add_short_term(self, role, content):
        """添加短期对话记忆"""
        self.short_term.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        # 保持短期记忆长度，防止 token 溢出
        if len(self.short_term) > 20:
            self.short_term.pop(0)

    def add_long_term(self, content, category="fact"):
        """添加长期记忆"""
        entry = {
            "content": content,
            "category": category,
            "created_at": datetime.now().isoformat()
        }
        self.long_term.append(entry)
        self._save_long_term()
        print(f"[Memory] 已固化长期记忆: {content[:20]}...")

    def get_recent_history(self, limit=5):
        """获取最近的对话历史 (用于 Prompt 上下文)"""
        return [{"role": m["role"], "content": m["content"]} for m in self.short_term[-limit:]]

    def get_relevant_long_term(self, query=None):
        """
        获取相关的长期记忆
        TODO: 未来可以接入向量检索
        目前简单返回所有长期记忆的文本摘要
        """
        if not self.long_term:
            return ""
        
        summary = "长期记忆:\n"
        for m in self.long_term[-5:]: # 只取最近5条长期记忆
            summary += f"- [{m['category']}] {m['content']}\n"
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
