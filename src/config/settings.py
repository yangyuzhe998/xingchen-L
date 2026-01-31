
import os
from dotenv import load_dotenv

load_dotenv(override=True)

class Settings:
    # 基础配置
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    
    # Moltbook
    MOLTBOOK_API_KEY = os.getenv("MOLTBOOK_API_KEY")
    MOLTBOOK_AGENT_NAME = os.getenv("MOLTBOOK_AGENT_NAME", "XingChen-V")
    MOLTBOOK_BASE_URL = "https://www.moltbook.com/api/v1"
    HEARTBEAT_INTERVAL = 3600 # 心跳间隔 (秒)

    # Memory
    MEMORY_STORAGE_PATH = os.path.join(PROJECT_ROOT, "src", "memory", "storage.json")
    VECTOR_DB_PATH = os.path.join(PROJECT_ROOT, "src", "memory", "chroma_db")
    SHORT_TERM_MAX_COUNT = 50
    SHORT_TERM_MAX_CHARS = 20000
    
    # EventBus
    BUS_DB_PATH = os.path.join(PROJECT_ROOT, "src", "memory", "bus.db")
    
    # S-Brain
    MAX_CODE_SCAN_SIZE = 50 * 1024 # 50KB

settings = Settings()
