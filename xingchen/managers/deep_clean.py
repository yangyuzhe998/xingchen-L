import sqlite3
import json
import os
import threading
import time
from datetime import datetime, timedelta
from xingchen.config.settings import settings
from xingchen.utils.llm_client import LLMClient
from xingchen.config.prompts import MEMORY_SUMMARY_PROMPT
from xingchen.utils.logger import logger


class DeepCleanManager:
    """
    深度维护管理器 (Deep Clean Manager)
    负责周期性地对记忆进行摘要、归档和剪枝。
    """
    def __init__(self, memory_service):
        self.memory_service = memory_service
        self.llm = LLMClient(provider="deepseek") 
        self.running = False
        self.last_clean_time = None
        
        # 路径配置
        self.state_path = os.path.join(settings.DATA_DIR, "deep_clean_state.json")
        self.archive_db_path = os.path.join(settings.DATA_DIR, "archive.db")
        
        self._load_state()
        self._init_archive_db()
        
        # 启动后台计时器
        self.timer_thread = threading.Thread(target=self._timer_loop, daemon=True)
        self.timer_thread.start()
        logger.info("[DeepClean] Manager initialized. Background timer started.")

    def _init_archive_db(self):
        """初始化冷存储 SQLite"""
        try:
            os.makedirs(os.path.dirname(self.archive_db_path), exist_ok=True)
            conn = sqlite3.connect(self.archive_db_path)
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
        if os.path.exists(self.state_path):
            try:
                with open(self.state_path, 'r') as f:
                    data = json.load(f)
                    time_str = data.get("last_clean_time")
                    if time_str:
                        self.last_clean_time = datetime.fromisoformat(time_str)
            except:
                pass

    def _save_state(self):
        """保存维护时间"""
        try:
            with open(self.state_path, 'w') as f:
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
                
                if not self.last_clean_time or (now - self.last_clean_time) > timedelta(hours=24):
                    if 3 <= now.hour < 4:
                        should_run = True
                    elif self.last_clean_time and (now - self.last_clean_time) > timedelta(hours=48):
                        logger.warning("[DeepClean] 检测到维护任务严重滞后，准备立即执行补救维护...")
                        should_run = True
                
                if should_run and not self.running:
                    self.perform_deep_clean("scheduled")
                
            except Exception as e:
                logger.error(f"[DeepClean] Timer loop error: {e}")
                
            time.sleep(300) # 每 5 分钟检查一次

    def perform_deep_clean(self, trigger_type="scheduled"):
        """
        执行深度维护 (耗时操作)
        """
        if self.running: return
        
        self.running = True
        logger.info(f"[DeepClean] 🧹 Starting deep maintenance ({trigger_type})...")
        
        try:
            # 1. 记忆压缩 (对最近 24 小时的长期记忆进行整合)
            self._consolidate_memories()
            
            # 2. 冷热分离 (将旧的、低频的原始记忆移入 SQLite 冷存储)
            self._archive_old_memories()
            
            # 3. 性格基准线修正 (根据日积月累的情绪波动永久性修正 Baseline)
            # 这部分通常在 Navigator.analyze_cycle 中触发增量，此处做大周期的整体归档

            self._save_state()
            logger.info("[DeepClean] ✨ Deep maintenance complete.")
            
        except Exception as e:
            logger.error(f"[DeepClean] Maintenance failed: {e}", exc_info=True)
        finally:
            self.running = False

    def _consolidate_memories(self):
        """整合长期记忆 (整合冗余 Facts)"""
        long_term = self.memory_service.long_term
        if len(long_term) < 50: return # 数量太少不整合
        
        # 1. 获取最近 24 小时或最近 50 条记忆
        recent_mems = long_term[-50:]
        context_str = "\n".join([f"- {m.content}" for m in recent_mems])
        
        # 2. 调用 LLM 整合
        prompt = MEMORY_SUMMARY_PROMPT.format(context=context_str)
        response_obj = self.llm.chat([{"role": "user", "content": prompt}])
        
        if response_obj:
            summary = response_obj.content
            if summary and len(summary) > 10:
                logger.info("[DeepClean] ✅ Memories consolidated.")
                # 将整合后的摘要存回长期记忆 (标记为 summary 类型)
                self.memory_service.add_long_term(f"[Summary] {summary}", category="summary")

    def _archive_old_memories(self):
        """将旧记忆移入冷存储 (SQLite)"""
        # 示例：保留最近 1000 条在 ChromaDB/JSON，其他的移入 SQLite
        # 此处简化实现，实际生产需更复杂的 LRU 策略
        pass
