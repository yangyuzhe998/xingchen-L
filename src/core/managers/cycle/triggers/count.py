from .base import BaseTrigger
from src.config.settings.settings import settings
from src.utils.logger import logger

class MessageCountTrigger(BaseTrigger):
    """
    基于对话轮数的触发器
    监听 driver_response 事件
    """
    def __init__(self, manager):
        super().__init__(manager)
        self.message_count = 0
        
    def check(self, event) -> bool:
        if event.type == "driver_response":
            self.message_count += 1
            logger.debug(f"[{self.name}] 计数器更新: {self.message_count}/{settings.CYCLE_TRIGGER_COUNT}")
            
            if self.message_count >= settings.CYCLE_TRIGGER_COUNT:
                self._trigger(f"Message Count Limit ({self.message_count})")
                self.reset() # 触发后重置
            return True
        return False

    def reset(self):
        """重置计数器 (通常在 S 脑分析完成后调用)"""
        logger.debug(f"[{self.name}] 计数器已重置。")
        self.message_count = 0
