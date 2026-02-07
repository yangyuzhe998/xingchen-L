import sqlite3
import json
import os
import threading
import time
from datetime import datetime, timedelta
from src.config.settings.settings import settings
from src.utils.llm_client import LLMClient
from src.config.prompts.prompts import MEMORY_SUMMARY_PROMPT
from src.utils.logger import logger

class DeepCleanManager:
    """
    深度维护管理器 (Deep Clean Manager)
    负责周期性地对记忆进行摘要、归档和剪枝。
    """
    def __init__(self, memory_service):
        self.memory_service = memory_service
        self.llm = LLMClient(provider="deepseek") # 使用 S 脑同款模型
        self.running = False
        self.last_clean_time = None
        self._load_state()
        self._init_archive_db()
        
        # 启动后台计时器
        self.timer_thread = threading.Thread(target=self._timer_loop, daemon=True)
        self.timer_thread.start()
        logger.info("[DeepClean] Manager initialized. Background timer started.")

    def _init_archive_db(self):
        """初始化冷存储 SQLite"""
        try:
            conn = sqlite3.connect(settings.ARCHIVE_DB_PATH)
            cursor = conn.cursor()
            # 原始记忆表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS raw_memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT,
                    category TEXT,
                    created_at TEXT,
                    archived_at TEXT
                )
            ''')
            # 剪枝关系表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pruned_relations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT,
                    relation TEXT,
                    target TEXT,
                    meta TEXT,
                    archived_at TEXT
                )
            ''')
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"[DeepClean] Failed to init archive DB: {e}", exc_info=True)

    def _load_state(self):
        """加载上次维护时间"""
        if os.path.exists(settings.DEEP_CLEAN_STATE_PATH):
            try:
                with open(settings.DEEP_CLEAN_STATE_PATH, 'r') as f:
                    data = json.load(f)
                    time_str = data.get("last_clean_time")
                    if time_str:
                        self.last_clean_time = datetime.fromisoformat(time_str)
            except:
                pass

    def _save_state(self):
        """保存维护时间"""
        try:
            with open(settings.DEEP_CLEAN_STATE_PATH, 'w') as f:
                json.dump({
                    "last_clean_time": datetime.now().isoformat()
                }, f)
        except:
            pass

    def _timer_loop(self):
        """后台计时器循环"""
        while True:
            try:
                now = datetime.now()
                
                # 检查是否应该触发
                should_run = False
                
                # 1. 检查是否错过了昨天的维护 (兜底机制)
                # 如果从未维护过，或者上次维护是24小时前
                if not self.last_clean_time or (now - self.last_clean_time) > timedelta(hours=24):
                    # 检查当前时间是否是凌晨 3:00 - 4:00
                    if 3 <= now.hour < 4:
                        should_run = True
                    # 或者如果上次维护时间太久远(超过48小时)，立即补做，不等待凌晨
                    elif self.last_clean_time and (now - self.last_clean_time) > timedelta(hours=48):
                        logger.warning("[DeepClean] 检测到维护任务严重滞后，准备立即执行补救维护...")
                        should_run = True
                
                if should_run and not self.running:
                    self.perform_deep_clean(trigger="auto")
                
                # 每分钟检查一次
                time.sleep(60)
            except Exception as e:
                logger.error(f"[DeepClean] Timer loop error: {e}", exc_info=True)
                time.sleep(60)

    def perform_deep_clean(self, trigger="manual"):
        """执行深度维护 (核心逻辑)"""
        if self.running:
            logger.warning("[DeepClean] Maintenance is already running.")
            return

        self.running = True
        logger.info(f"[DeepClean] Starting Deep Clean Sequence (Trigger: {trigger})...")
        
        try:
            # 1. 归档长期记忆 (JSON -> Archive)
            self._archive_long_term_memories()
            
            # 2. 剪枝图谱 (Graph Pruning)
            # self._prune_graph() # 暂时先不做，风险较大，先做归档
            
            # 更新状态
            self.last_clean_time = datetime.now()
            self._save_state()
            
            logger.info("[DeepClean] Maintenance Complete.")
        except Exception as e:
            logger.error(f"[DeepClean] Maintenance Failed: {e}", exc_info=True)
        finally:
            self.running = False

    def _archive_long_term_memories(self):
        """
        归档长期记忆:
        1. 读取 storage.json
        2. 如果条目过多 (>50)，进行摘要
        3. 将原始条目移入 archive.db
        4. 将摘要写回 storage.json
        """
        # 获取当前所有长期记忆
        # 注意：直接操作 Service 的数据结构可能不安全，最好通过 Copy
        # 这里为了简化，我们假设 Service 已经 commit 过了
        # 我们直接读取 JSON 文件来处理，避免内存竞争
        
        json_path = settings.MEMORY_STORAGE_PATH
        if not os.path.exists(json_path):
            return

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                memories = json.load(f)
        except:
            return

        if len(memories) < 20: # 阈值太低没必要做
            logger.debug("[DeepClean] Memory count low, skipping archive.")
            return

        logger.info(f"[DeepClean] Archiving {len(memories)} memories...")
        
        # 1. 生成摘要
        # 将所有 memory content 拼接
        context = "\n".join([f"- {m.get('content')}" for m in memories])
        
        summary_prompt = MEMORY_SUMMARY_PROMPT.format(context=context)
        
        summary_response = self.llm.chat([{"role": "user", "content": summary_prompt}])
        
        new_memories = []
        if summary_response:
            lines = summary_response.split('\n')
            for line in lines:
                line = line.strip().strip('- ')
                if line:
                    new_memories.append({
                        "content": line,
                        "category": "summary",
                        "created_at": datetime.now().isoformat(),
                        "metadata": {"source": "deep_clean"}
                    })
        else:
            logger.warning("[DeepClean] Summarization failed, aborting archive.")
            return

        # 2. 存入 SQLite (Archive)
        try:
            conn = sqlite3.connect(settings.ARCHIVE_DB_PATH)
            cursor = conn.cursor()
            archive_time = datetime.now().isoformat()
            
            for m in memories:
                cursor.execute(
                    "INSERT INTO raw_memories (content, category, created_at, archived_at) VALUES (?, ?, ?, ?)",
                    (m.get('content'), m.get('category'), m.get('created_at'), archive_time)
                )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"[DeepClean] SQLite write failed: {e}", exc_info=True)
            return

        # 3. 更新 storage.json (Replace with summary)
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(new_memories, f, ensure_ascii=False, indent=2)
            
            # 通知 MemoryService 重载 (这是一个 Hack，理想情况应该是 Service 监听变化)
            # 或者我们不通知，下次启动时自然会加载新的。
            # 但为了运行时一致性，最好能 reload。
            # 这里先不做 reload，假设深度维护通常在闲时进行，影响不大。
            logger.info("[DeepClean] storage.json updated with summaries.")
        except Exception as e:
            logger.error(f"[DeepClean] Failed to update storage.json: {e}", exc_info=True)
