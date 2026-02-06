import threading
import time
from .base import BaseTrigger
from src.config.settings.settings import settings
from src.utils.logger import logger
from src.core.bus.event_bus import event_bus, Event
from src.schemas.events import SystemHeartbeatPayload

class IdleTrigger(BaseTrigger):
    """
    基于空闲时间的触发器
    维护后台监控线程
    """
    def __init__(self, manager):
        super().__init__(manager)
        self.last_activity_time = time.time()
        self.running = False
        self.monitor_thread = None

    def start(self):
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info(f"[{self.name}] 空闲监控线程已启动 (Timeout: {settings.CYCLE_IDLE_TIMEOUT}s)")

    def stop(self):
        self.running = False
        if self.monitor_thread:
            # 这里的 join 可能需要 timeout，防止阻塞
            # 但作为 daemon 线程，其实可以直接不管
            pass

    def check(self, event) -> bool:
        # 任何用户输入或 Driver 响应都视为“活动”
        if event.type in ["user_input", "driver_response"]:
            self.last_activity_time = time.time()
            # logger.debug(f"[{self.name}] 活动时间已更新")
        return False

    def reset(self):
        """重置计时器 (在 S 脑分析后调用)"""
        self.last_activity_time = time.time()

    def _monitor_loop(self):
        while self.running:
            time.sleep(settings.IDLE_MONITOR_INTERVAL)
            
            # 计算空闲时间
            idle_time = time.time() - self.last_activity_time
            
            if idle_time > settings.CYCLE_IDLE_TIMEOUT:
                logger.info(f"[{self.name}] 系统空闲超时 ({idle_time:.1f}s > {settings.CYCLE_IDLE_TIMEOUT}s)")
                
                # 注入心跳事件，确保 S脑 有米下锅 (保持原逻辑)
                event_bus.publish(Event(
                    type="system_heartbeat",
                    source="cycle_manager", # 保持 source 不变，或者改为 idle_trigger
                    payload=SystemHeartbeatPayload(content="系统已空闲一段时间。S脑需自发思考当前状态或决定是否进行社交活动。"),
                    meta={}
                ))
                
                self._trigger(f"System Idle Timeout ({settings.CYCLE_IDLE_TIMEOUT}s)")
                # 触发后重置，防止连续触发
                self.reset()
