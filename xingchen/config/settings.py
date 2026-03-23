import os
from dotenv import load_dotenv

load_dotenv(override=True)

class Settings:
    # 基础配置
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    
    # 路径配置
    DATA_DIR = os.path.join(PROJECT_ROOT, "data")
    LOG_DIR = os.path.join(PROJECT_ROOT, "logs")
    LOG_FILE = os.path.join(LOG_DIR, "xingchen.log")
    LOG_LEVEL = "INFO"
    
    # 记忆存储路径
    MEMORY_STORAGE_PATH = os.path.join(DATA_DIR, "storage.json")
    VECTOR_DB_PATH = os.path.join(DATA_DIR, "chroma_db")
    DIARY_PATH = os.path.join(DATA_DIR, "diary.md")
    KNOWLEDGE_DB_PATH = os.path.join(DATA_DIR, "knowledge.db")
    GRAPH_DB_PATH = os.path.join(DATA_DIR, "knowledge.db") # v3.0 统一使用 KnowledgeDB
    ALIAS_MAP_PATH = os.path.join(DATA_DIR, "knowledge.db") # v3.0 统一使用 KnowledgeDB
    ARCHIVE_DB_PATH = os.path.join(DATA_DIR, "archive.db")
    BUS_DB_PATH = os.path.join(DATA_DIR, "bus.db")
    WAL_PATH = os.path.join(DATA_DIR, "wal.log")
    PSYCHE_DEFAULT_STATE_FILE = os.path.join(DATA_DIR, "psyche_state.json")
    MIND_LINK_STORAGE_PATH = os.path.join(DATA_DIR, "mind_link_buffer.json")
    SHORT_TERM_CACHE_PATH = os.path.join(DATA_DIR, "short_term_cache.json")
    
    # 记忆参数
    SHORT_TERM_MAX_COUNT = 30
    SHORT_TERM_MAX_CHARS = 20000
    DEFAULT_SHORT_TERM_LIMIT = 10
    DEFAULT_LONG_TERM_LIMIT = 5
    DEFAULT_ALIAS_LIMIT = 5
    EMOTIONAL_RESONANCE_FACTOR = 0.1 # 触景生情系数
    
    # 心智引擎参数
    PSYCHE_DECAY_RATE = 0.05
    BASELINE_DRIFT_PERSISTENCE = 0.02 # 漂移因子
    BASELINE_DRIFT_THRESHOLD = 0.2    # 漂移阈值
    INTUITION_WEAKEN_SECONDS = 3600   # 潜意识衰减秒数
    EXPIRE_SECONDS = 7200             # 潜意识过期秒数
    
    # 周期管理
    CYCLE_TRIGGER_COUNT = 5
    CYCLE_CHECK_INTERVAL = 0.5
    CYCLE_IDLE_TIMEOUT = 300
    IDLE_MONITOR_INTERVAL = 10
    NAVIGATOR_DELAY_SECONDS = 5
    NAVIGATOR_EVENT_LIMIT = 50
    
    # 对话与主动交互
    PROACTIVE_COOLDOWN = 60
    CONTEXT_HISTORY_WINDOW = 15 # 上下文历史窗口
    MAX_TOOL_CALL_ROUNDS = 3    # LLM 工具循环最大次数
    PROACTIVE_HISTORY_WINDOW = 10
    
    # LLM 配置
    DEFAULT_LLM_PROVIDER = "deepseek"
    DEFAULT_LLM_MODEL = "deepseek-chat"
    DEFAULT_LLM_TIMEOUT = 180
    
    F_BRAIN_MODEL = "qwen-max"
    S_BRAIN_MODEL = "deepseek-reasoner"
    
    # LLM 默认模型 (从 llm_client.py 抽离)
    ZHIPU_DEFAULT_MODEL = "glm-4"
    QWEN_DEFAULT_MODEL = "qwen-turbo"
    
    # 工具与 Shell 配置 (从 system_tools.py 抽离)
    SHELL_DANGEROUS_COMMANDS = [
        "rm ", "del ", "remove-item", "format-", 
        "reg ", "net user", "shutdown", "restart",
        "rmdir", "rd ", "wget", "curl", "Invoke-WebRequest"
    ]
    SHELL_EXECUTABLE = "powershell" if os.name == "nt" else "bash"
    SHELL_OUTPUT_MAX_CHARS = 1000
    
    # Web 安全
    WEB_API_KEY = os.getenv("WEB_API_KEY", "default_secret_key_change_me")
    
    # 沙箱限制
    SANDBOX_MEM_LIMIT = "128m"
    SANDBOX_CPU_LIMIT = 500000000
    SANDBOX_TIMEOUT = 30

settings = Settings()
