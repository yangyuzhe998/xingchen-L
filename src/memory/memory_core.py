from .storage.vector import ChromaStorage
from .storage.local import JsonStorage
from .storage.diary import DiaryStorage
from .services.memory_service import MemoryService
from ..config.settings.settings import settings

class Memory:
    """
    记忆模块 Facade (兼容旧接口)
    """
    def __init__(self, 
                 storage_path=None, 
                 vector_db_path=None, 
                 diary_path=None):
        
        # 使用 settings 中的默认值，如果未提供参数
        self.vector_storage = ChromaStorage(vector_db_path or settings.VECTOR_DB_PATH)
        self.json_storage = JsonStorage(storage_path or settings.MEMORY_STORAGE_PATH)
        self.diary_storage = DiaryStorage(diary_path or settings.DIARY_PATH)
        
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

    def get_skill_collection(self):
        return self.service.get_skill_collection()

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
