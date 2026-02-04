from .storage.vector import ChromaStorage
from .storage.local import JsonStorage
from .storage.diary import DiaryStorage
from .storage.graph import GraphMemory
from .services.memory_service import MemoryService
from ..config.settings.settings import settings

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
        
        self.service = MemoryService(self.vector_storage, self.json_storage, self.diary_storage)
        
        # 兼容旧属性访问
        self.short_term = self.service.short_term
        self.long_term = self.service.long_term
        self.navigator = None

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
        
    def search_alias(self, query, limit=1, threshold=0.4):
        return self.service.search_alias(query, limit, threshold)

    def add_short_term(self, role, content):
        self.service.add_short_term(role, content)
        # 同步属性引用 (虽然 list 是引用类型，通常不需要，但为了保险)
        self.short_term = self.service.short_term
        
        # 检查是否需要压缩 (逻辑复刻)
        MAX_COUNT = 50
        if len(self.short_term) > MAX_COUNT:
            if self.navigator:
                print("[Memory] 短期记忆已满，请求 S脑 压缩...")
                self.navigator.request_diary_generation()

    def get_recent_history(self, limit=10):
        return self.service.get_recent_history(limit)

    def get_relevant_long_term(self, query=None, limit=5, search_mode="keyword"):
        return self.service.get_relevant_long_term(query, limit, search_mode)

    def add_long_term(self, content, category="fact"):
        self.service.add_long_term(content, category)
        self.long_term = self.service.long_term
        
    def save_short_term_cache(self):
        self.service.save_cache()

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
                print(f"[Memory] 认知图谱保存失败: {e}")
        
        # 2. 调用 Service 的保存逻辑 (Json, Cache) - 内部也有 dirty check
        self.service.force_save_all()
