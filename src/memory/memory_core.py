from .storage.vector import ChromaStorage
from .storage.local import JsonStorage
from .storage.diary import DiaryStorage
from .storage.graph import GraphMemory
from .storage.write_ahead_log import WriteAheadLog
from .services.memory_service import MemoryService
from ..config.settings.settings import settings
from ..utils.logger import logger
from ..core.bus.event_bus import event_bus
from ..schemas.events import BaseEvent as Event, SystemHeartbeatPayload
from typing import Dict, Optional

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
        self.graph_storage = GraphMemory(graph_path or settings.GRAPH_DB_PATH)
        
        # [Fix P0-1] 初始化 WAL (Write-Ahead Log)
        self.wal = WriteAheadLog()
        
        self.service = MemoryService(self.vector_storage, self.json_storage, self.diary_storage)
        
        self.navigator = None
        
        # [Fix P0-1] 启动时重放 WAL，恢复未提交的数据
        self._replay_wal()

    @property
    def short_term(self):
        return self.service.short_term

    @property
    def long_term(self):
        return self.service.long_term

    def set_navigator(self, navigator):
        self.navigator = navigator
        # 如果 service 需要 navigator，也可以传递进去
        # self.service.set_navigator(navigator)

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
        
    def save_alias(self, alias, target_entity):
        self.service.save_alias(alias, target_entity)
        
    def search_alias(self, query, limit=None, threshold=None):
        if limit is None:
            limit = settings.DEFAULT_ALIAS_LIMIT
        if threshold is None:
            threshold = settings.DEFAULT_ALIAS_THRESHOLD
        return self.service.search_alias(query, limit, threshold)

    def add_short_term(self, role, content):
        # [Fix P0-1] 先写 WAL，再执行操作
        try:
            self.wal.append("add_short_term", {"role": role, "content": content})
        except Exception as e:
            logger.error(f"[Memory] WAL 写入失败: {e}", exc_info=True)
            # WAL 失败不应阻止操作，但要记录
        
        self.service.add_short_term(role, content)
        # 同步属性引用 (虽然 list 是引用类型，通常不需要，但为了保险)
        # self.short_term = self.service.short_term (Deprecated: short_term is now a property)
        
        # 检查是否需要压缩 (逻辑复刻)
        if len(self.short_term) > settings.SHORT_TERM_MAX_COUNT:
            logger.info(f"[Memory] 短期记忆已达阈值({settings.SHORT_TERM_MAX_COUNT})，发布 memory_full 事件...")
            self.save_short_term_cache()
            
            # 发布事件通知 CycleManager/Navigator
            event_bus.publish(Event(
                type="system_notification",
                source="memory",
                payload={"type": "memory_full", "count": len(self.short_term)},
                meta={}
            ))

    def clear_short_term(self):
        """清空短期记忆 (Facade)"""
        self.service.clear_short_term()

    def get_recent_history(self, limit=10):
        return self.service.get_recent_history(limit)

    def get_relevant_long_term(self, query=None, limit=5, search_mode="keyword"):
        return self.service.get_relevant_long_term(query, limit, search_mode)

    def add_long_term(self, content, category="fact"):
        # [Fix P0-1] 先写 WAL
        try:
            self.wal.append("add_long_term", {"content": content, "category": category})
        except Exception as e:
            logger.error(f"[Memory] WAL 写入失败: {e}", exc_info=True)
        
        self.service.add_long_term(content, category)
        # self.long_term = self.service.long_term (Deprecated)

    def add_triplet(self, source: str, relation: str, target: str, weight: float = 1.0, meta: Dict = None, relation_type: str = "general"):
        """添加知识图谱三元组"""
        if self.graph_storage:
            self.graph_storage.add_triplet(source, relation, target, weight, meta, relation_type)

    def save_graph(self, force=False):
        """保存知识图谱"""
        if self.graph_storage:
            self.graph_storage.save(force)
        
    def save_short_term_cache(self):
        """
        保存短期记忆缓存
        注意：此处不应清空 WAL，因为 WAL 可能包含未提交的 LongTermMemory。
        只有在 force_save_all 中确保所有数据都持久化后，才能清空 WAL。
        """
        self.service.save_cache()
        # [Fix] 移除不安全的 WAL 清空逻辑
        # if self.wal.get_entry_count() > 0:
        #     self.wal.clear()

    def commit_long_term(self):
        self.service.commit_long_term()
        
    def commit_short_term(self):
        self.service.commit_short_term()
        
    def force_save_all(self):
        """
        统一强制保存入口 (Smart Commit)
        """
        # 1. 保存 Graph (GraphMemory 内部有 dirty check)
        if self.graph_storage:
            try:
                # save() 内部会检查 _dirty
                self.graph_storage.save()
            except Exception as e:
                logger.error(f"[Memory] 认知图谱保存失败: {e}", exc_info=True)
        
        # 2. 调用 Service 的保存逻辑 (Json, Cache) - 内部也有 dirty check
        self.service.force_save_all()
        
        # [Fix P0-1] 3. 成功保存后清空 WAL
        try:
            self.wal.clear()
            logger.info("[Memory] WAL 已清空 (数据已持久化)")
        except Exception as e:
            logger.error(f"[Memory] WAL 清空失败: {e}", exc_info=True)
    
    def _replay_wal(self):
        """
        [Fix P0-1] 启动时重放 WAL，恢复未提交的数据
        
        智能恢复策略：
        1. Cache 已加载的数据不重复恢复
        2. 只恢复比 Cache 最后一条更新的操作
        3. 避免重复数据
        """
        try:
            entries = self.wal.replay()
            if not entries:
                logger.info("[Memory] WAL 为空，无需恢复")
                return
            
            # 获取 Cache 中最后一条记忆的时间戳
            last_cache_timestamp = None
            if self.service.short_term:
                # Cache 已经加载了数据
                last_entry = self.service.short_term[-1]
                last_cache_timestamp = last_entry.timestamp
                logger.info(f"[Memory] Cache 最后一条记忆时间: {last_cache_timestamp}")
            
            logger.info(f"[Memory] 开始智能恢复 WAL ({len(entries)} 条操作)...")
            recovered_count = 0
            skipped_count = 0
            
            for entry in entries:
                operation = entry.get("operation")
                data = entry.get("data", {})
                entry_time = entry.get("datetime")  # ISO format timestamp from WAL
                
                # 如果 Cache 有数据，且 WAL 条目时间早于或等于 Cache 最后一条，跳过
                if last_cache_timestamp and entry_time:
                    if entry_time <= last_cache_timestamp:
                        skipped_count += 1
                        continue
                
                try:
                    if operation == "add_short_term":
                        role = data.get("role")
                        content = data.get("content")
                        if role and content:
                            # 直接调用 service，不再触发 WAL 写入
                            self.service.add_short_term(role, content)
                            recovered_count += 1
                    
                    elif operation == "add_long_term":
                        content = data.get("content")
                        category = data.get("category", "fact")
                        if content:
                            self.service.add_long_term(content, category)
                            recovered_count += 1
                    
                    else:
                        logger.warning(f"[Memory] 未知操作类型: {operation}")
                
                except Exception as e:
                    logger.error(f"[Memory] 恢复操作失败: {operation}, {e}", exc_info=True)
            
            if skipped_count > 0:
                logger.info(f"[Memory] 跳过 {skipped_count} 条已在 Cache 中的操作")
            
            logger.info(f"[Memory] 恢复完成，成功恢复 {recovered_count}/{len(entries)} 条新操作")
            
            # 恢复后立即保存，并清空 WAL
            if recovered_count > 0:
                self.force_save_all()
            else:
                # 即使没有恢复新数据，也清空 WAL（因为都在 Cache 里了）
                self.wal.clear()
                logger.info("[Memory] WAL 已清空（无新数据需恢复）")
            
        except Exception as e:
            logger.error(f"[Memory] WAL 重放失败: {e}", exc_info=True)
