from .base import BaseTrigger
from src.utils.logger import logger

class MemoryFullTrigger(BaseTrigger):
    """
    基于内存满载通知的触发器
    监听 system_notification
    """
    def check(self, event) -> bool:
        if event.type == "system_notification":
            payload = event.payload_data
            if payload.get("type") == "memory_full":
                count = payload.get("count", "N/A")
                logger.info(f"[{self.name}] 收到 Memory Full 信号 ({count})")
                
                # 注意：这里触发的是 compression 任务
                self._trigger("Memory Full Notification", task_type="compression")
                return True
        return False
