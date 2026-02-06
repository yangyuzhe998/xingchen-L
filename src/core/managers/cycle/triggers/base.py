from abc import ABC, abstractmethod
from src.utils.logger import logger

class BaseTrigger(ABC):
    """
    S脑触发器基类
    """
    def __init__(self, manager):
        self.manager = manager
        self.name = self.__class__.__name__
        logger.info(f"[{self.name}] 触发器已初始化。")

    @abstractmethod
    def check(self, event) -> bool:
        """
        检查事件是否满足触发条件
        :param event: EventBus 事件
        :return: 是否已处理 (部分触发器可能消费事件)
        """
        pass

    def start(self):
        """启动后台任务 (如果需要)"""
        pass

    def stop(self):
        """停止后台任务 (如果需要)"""
        pass

    def _trigger(self, reason: str, task_type: str = "reasoning"):
        """
        执行触发
        :param reason: 触发原因
        :param task_type: 任务类型 (reasoning / compression)
        """
        logger.info(f"[{self.name}] 🔥 触发 S 脑! 原因: {reason} (Task: {task_type})")
        if task_type == "reasoning":
            self.manager.trigger_reasoning(reason)
        elif task_type == "compression":
            self.manager.trigger_compression(reason)
