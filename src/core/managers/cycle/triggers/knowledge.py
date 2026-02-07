
import threading
import time
import os
import glob
from .base import BaseTrigger
from src.config.settings.settings import settings
from src.utils.logger import logger

class KnowledgeTrigger(BaseTrigger):
    """
    知识内化触发器
    监控 storage/knowledge_staging 目录，发现文件时触发内化任务
    """
    def __init__(self, manager):
        super().__init__(manager)
        self.running = False
        self.monitor_thread = None
        self.staging_dir = os.path.join(settings.PROJECT_ROOT, "storage", "knowledge_staging")
        # 监控间隔 (秒)
        self.check_interval = 30 
        
    def start(self):
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info(f"[{self.name}] 知识暂存区监控已启动 (Interval: {self.check_interval}s)")

    def stop(self):
        self.running = False
        # thread is daemon, will exit with main process

    def check(self, event) -> bool:
        # 本触发器主要依赖后台轮询，不消费特定事件
        # 但可以在收到特定事件（如 web_crawl 完成）时立即检查，目前暂不需要
        return False

    def _monitor_loop(self):
        while self.running:
            try:
                # 检查目录是否存在文件
                if os.path.exists(self.staging_dir):
                    files = glob.glob(os.path.join(self.staging_dir, "*.md"))
                    if files:
                        count = len(files)
                        logger.debug(f"[{self.name}] 发现 {count} 个待内化文档...")
                        self._trigger(f"Found {count} files in staging", task_type="internalization")
                        
                        # 触发后等待较长时间，避免频繁触发 (Navigator 内部也有锁)
                        time.sleep(self.check_interval * 2)
                        continue
            except Exception as e:
                logger.error(f"[{self.name}] 监控出错: {e}")
            
            time.sleep(self.check_interval)
