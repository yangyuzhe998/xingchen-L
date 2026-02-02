
import os
from dotenv import load_dotenv

load_dotenv(override=True)

class Settings:
    # 基础配置
    # Note: __file__ is now src/config/settings/settings.py
    # So PROJECT_ROOT is ../../../..
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    
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
    
    SHORT_TERM_MAX_COUNT = 50
    SHORT_TERM_MAX_CHARS = 20000
    
    # EventBus
    BUS_DB_PATH = os.path.join(MEMORY_DATA_DIR, "bus.db")
    
    # S-Brain
    MAX_CODE_SCAN_SIZE = 50 * 1024 # 50KB
    CYCLE_TRIGGER_COUNT = 5 # 对话轮数阈值
    CYCLE_CHECK_INTERVAL = 0.5 # 监控轮询间隔 (秒)
    CYCLE_IDLE_TIMEOUT = 60 # 空闲强制分析阈值 (秒)

    # Psyche Engine
    PSYCHE_DECAY_RATE = 0.05 # 状态自然衰减率
    PSYCHE_DEFAULT_STATE_FILE = os.path.join(MEMORY_DATA_DIR, "psyche_state.json")
    MIND_LINK_STORAGE_PATH = os.path.join(MEMORY_DATA_DIR, "mind_link_buffer.json")

    # LLM Defaults
    DEFAULT_LLM_PROVIDER = "deepseek"
    DEFAULT_LLM_MODEL = "deepseek-chat"
    DEFAULT_LLM_TIMEOUT = 180

    # Sandbox
    SANDBOX_MEM_LIMIT = "128m"
    SANDBOX_CPU_LIMIT = 500000000 # 0.5 CPU
    SANDBOX_TIMEOUT = 30 # 秒

settings = Settings()
