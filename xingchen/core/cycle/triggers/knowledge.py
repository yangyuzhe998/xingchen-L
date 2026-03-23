import threading
import time
import os
import glob
from .base import BaseTrigger
from xingchen.config.settings import settings
from xingchen.utils.logger import logger


class KnowledgeTrigger(BaseTrigger):
    """
    知识内化触发器
    监控 data/knowledge_staging 目录，发现文件时触发内化任务
    """
    def __init__(self, manager):
        super().__init__(manager)
        self.running = False
        self.monitor_thread = None
        self.staging_dir = os.path.join(settings.DATA_DIR, "knowledge_staging")
        # 监控间隔 (秒)
        self.check_interval = 30 
        
    def start(self):
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info(f"[{self.name}] 知识暂存区监控已启动 (Interval: {self.check_interval}s)")

    def stop(self):
        self.running = False

    def check(self, event) -> bool:
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
                        
                        # 触发后等待较长时间，避免频繁触发
                        time.sleep(self.check_interval * 2)
                        continue
            except Exception as e:
                logger.error(f"[{self.name}] 监控出错: {e}")
            
            time.sleep(self.check_interval)
