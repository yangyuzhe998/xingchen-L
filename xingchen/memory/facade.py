from typing import Dict, Optional, List
from xingchen.memory.storage.vector import ChromaStorage
from xingchen.memory.storage.local import JsonStorage
from xingchen.memory.storage.diary import DiaryStorage
from xingchen.memory.storage.graph import GraphMemory
from xingchen.memory.storage.knowledge_db import KnowledgeDB
from xingchen.memory.wal import WriteAheadLog
from xingchen.memory.service import MemoryService
from xingchen.config.settings import settings
from xingchen.utils.logger import logger
from xingchen.core.event_bus import event_bus
from xingchen.schemas.events import BaseEvent as Event


class Memory:
    """
    记忆模块 Facade (兼容旧接口)
    """
    def __init__(self, 
                 storage_path=None, 
                 vector_db_path=None, 
                 diary_path=None,
                 graph_path=None):
        
        # 使用 settings 中的默认值，如果未提供参数
        self.vector_storage = ChromaStorage(vector_db_path or settings.VECTOR_DB_PATH)
        self.json_storage = JsonStorage(storage_path or settings.MEMORY_STORAGE_PATH)
        self.diary_storage = DiaryStorage(diary_path or settings.DIARY_PATH)
        self.graph_storage = GraphMemory(graph_path)
        
        # 初始化 WAL (预写日志) 用于崩溃恢复
        self.wal = WriteAheadLog()
        
        # MemoryService 会自动初始化 KnowledgeDB 单例
        self.service = MemoryService(self.vector_storage, self.json_storage, self.diary_storage)
        
        self.navigator = None
        
        # 订阅事件总线以响应调试请求
        event_bus.subscribe(self._on_event)
        
        # 启动时重放 WAL，恢复未提交的数据
        self._replay_wal()

    def _on_event(self, event):
        """处理事件总线消息"""
        if event.type == "debug_request":
            payload = event.payload_data
            action = payload.get("action")
            if action == "dump_short_term":
                self._handle_dump_short_term()

    def _handle_dump_short_term(self):
        """处理短期记忆转储请求"""
        try:
            data = [entry.to_dict() for entry in self.short_term]
            event_bus.publish(Event(
                type="debug_response",
                source="memory",
                payload={
                    "action": "dump_short_term",
                    "data": data
                },
                meta={}
            ))
        except Exception as e:
            logger.error(f"[Memory] Dump short term failed: {e}")

    @property
    def short_term(self):
        return self.service.short_term

    @property
    def long_term(self):
        return self.service.long_term

    @property
    def knowledge_db(self):
        """从 Service 层暴露 KnowledgeDB"""
        return self.service.knowledge_db

    def set_navigator(self, navigator):
        self.navigator = navigator

    def write_diary_entry(self, content):
        self.service.write_diary_entry(content)

    def get_command_cases_collection(self):
        return self.service.get_command_cases_collection()

    def get_command_docs_collection(self):
        return self.service.get_command_docs_collection()
        
    def get_skill_collection(self):
        return self.service.get_skill_collection()

    def get_alias_collection(self):
        return self.service.get_alias_collection()

    def search_alias(self, query, limit=None):
        return self.service.search_alias(query, limit)

    def get_relevant_long_term(self, query=None, limit=None, search_mode="keyword"):
        return self.service.get_relevant_long_term(query, limit, search_mode)

    def get_recent_history(self, limit=None):
        return self.service.get_recent_history(limit)

    def add_short_term(self, role, content):
        self.service.add_short_term(role, content)

    def clear_short_term(self):
        self.service.clear_short_term()

    def add_long_term(self, content, category="fact"):
        # 写入 WAL
        self.wal.append("add_long_term", {"content": content, "category": category})
        self.service.add_long_term(content, category)

    def save_cache(self):
        self.service.save_cache()

    def commit_long_term(self):
        self.service.commit_long_term()
        # 成功保存后清理 WAL
        self.wal.clear()

    def _replay_wal(self):
        """重放 WAL 日志"""
        entries = self.wal.replay()
        if not entries:
            return
            
        for entry in entries:
            op = entry.get("operation")
            data = entry.get("data")
            if op == "add_long_term":
                # 直接通过 service 添加，跳过 WAL 递归写入
                self.service.add_long_term(data["content"], data["category"])
        
        logger.info(f"[Memory] WAL 重放完成，成功恢复 {len(entries)} 条操作。")
        self.commit_long_term()
