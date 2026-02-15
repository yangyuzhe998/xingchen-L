
import os
from dotenv import load_dotenv

load_dotenv(override=True)

class Settings:
    # 基础配置
    # Note: __file__ is now src/config/settings/settings.py
    # So PROJECT_ROOT is ../../../..
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    
    # Logging
    LOG_DIR = os.path.join(PROJECT_ROOT, "logs")
    LOG_FILE = os.path.join(LOG_DIR, "xingchen.log")
    LOG_LEVEL = "INFO"
    
    # Moltbook (Deprecated)
    # MOLTBOOK_API_KEY = os.getenv("MOLTBOOK_API_KEY")
    # MOLTBOOK_AGENT_NAME = os.getenv("MOLTBOOK_AGENT_NAME", "XingChen-V")
    # MOLTBOOK_BASE_URL = "https://www.moltbook.com/api/v1"
    # HEARTBEAT_INTERVAL = 3600 # 心跳间隔 (秒)

    # Memory
    MEMORY_DATA_DIR = os.path.join(PROJECT_ROOT, "src", "memory_data")
    MEMORY_STORAGE_PATH = os.path.join(MEMORY_DATA_DIR, "storage.json")
    VECTOR_DB_PATH = os.path.join(MEMORY_DATA_DIR, "chroma_db")
    DIARY_PATH = os.path.join(MEMORY_DATA_DIR, "diary.md")
    
    # [Refactored] Graph & Alias are now in KnowledgeDB (SQLite)
    # NOTE: tests still expect these legacy paths to exist.
    GRAPH_DB_PATH = os.path.join(MEMORY_DATA_DIR, "graph.db")
    ALIAS_MAP_PATH = os.path.join(MEMORY_DATA_DIR, "alias_map.json")

    KNOWLEDGE_DB_PATH = os.path.join(MEMORY_DATA_DIR, "knowledge.db")
    
    ARCHIVE_DB_PATH = os.path.join(MEMORY_DATA_DIR, "archive.db") # Cold Storage
    DEEP_CLEAN_STATE_PATH = os.path.join(MEMORY_DATA_DIR, "deep_clean_state.json") # Maintenance State
    SHORT_TERM_CACHE_PATH = os.path.join(MEMORY_DATA_DIR, "short_term_cache.json")
    WAL_PATH = os.path.join(MEMORY_DATA_DIR, "wal.log")
    
    SHORT_TERM_MAX_COUNT = 30
    SHORT_TERM_MAX_CHARS = 20000
    
    # Retrieval Defaults
    DEFAULT_SHORT_TERM_LIMIT = 10
    DEFAULT_LONG_TERM_LIMIT = 5
    DEFAULT_ALIAS_LIMIT = 1
    DEFAULT_ALIAS_THRESHOLD = 0.4
    
    # EventBus
    BUS_DB_PATH = os.path.join(MEMORY_DATA_DIR, "bus.db")
    
    # S-Brain
    MAX_CODE_SCAN_SIZE = 50 * 1024 # 50KB
    CYCLE_TRIGGER_COUNT = 5 # 对话轮数阈值
    CYCLE_CHECK_INTERVAL = 0.5 # 监控轮询间隔 (秒)
    CYCLE_IDLE_TIMEOUT = 300 # 空闲强制分析阈值 (秒)
    IDLE_MONITOR_INTERVAL = 10 # 空闲监控循环间隔 (秒)
    NAVIGATOR_DELAY_SECONDS = 5 # 记忆压缩延迟时间 (秒)
    NAVIGATOR_EVENT_LIMIT = 50 # 记忆压缩时获取的事件数量上限
    
    # Proactive Interaction
    PROACTIVE_COOLDOWN = 60 # 主动发言冷却时间 (秒)
    PROACTIVE_HISTORY_WINDOW = 10 # 检查重复话题的历史窗口大小

    # Psyche Engine
    PSYCHE_DECAY_RATE = 0.05 # 状态自然衰减率
    PSYCHE_DEFAULT_STATE_FILE = os.path.join(MEMORY_DATA_DIR, "psyche_state.json")
    MIND_LINK_STORAGE_PATH = os.path.join(MEMORY_DATA_DIR, "mind_link_buffer.json")

    # LLM Defaults
    DEFAULT_LLM_PROVIDER = "deepseek"
    DEFAULT_LLM_MODEL = "deepseek-chat"
    DEFAULT_LLM_TIMEOUT = 180
    
    # Brain Models
    F_BRAIN_MODEL = "qwen-max"
    S_BRAIN_MODEL = "deepseek-reasoner"

    # Sandbox
    SANDBOX_MEM_LIMIT = "128m"
    SANDBOX_CPU_LIMIT = 500000000 # 0.5 CPU
    SANDBOX_TIMEOUT = 30 # 秒

settings = Settings()


