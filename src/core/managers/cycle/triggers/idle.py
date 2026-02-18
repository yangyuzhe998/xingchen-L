import threading
import time
from .base import BaseTrigger
from src.config.settings.settings import settings
from src.utils.logger import logger
from src.core.bus.event_bus import event_bus, Event
from src.schemas.events import SystemHeartbeatPayload
from src.psyche import psyche_engine

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

    def _decide_idle_action(self) -> str:
        """根据心智状态决定空闲动作 (Phase 5.1)"""
        try:
            state = psyche_engine.get_raw_state()
            dims = state.get("dimensions", {})
            
            laziness = dims.get("laziness", {}).get("value", 0.0)
            curiosity = dims.get("curiosity", {}).get("value", 0.0)
            intimacy = dims.get("intimacy", {}).get("value", 0.0)

            if laziness > 0.7:
                return "sleep"  # 懒惰高，继续休眠
            
            if curiosity > 0.6:
                return "exploration"  # 好奇高，自主探索新知识
            
            if intimacy > 0.5:
                return "connection"  # 亲密高，想找用户聊天
                
        except Exception as e:
            logger.error(f"[{self.name}] 决策空闲动作失败: {e}")
            
        return "heartbeat"  # 默认发送普通心跳

    def _monitor_loop(self):
        while self.running:
            time.sleep(settings.IDLE_MONITOR_INTERVAL)
            
            # 计算空闲时间
            idle_time = time.time() - self.last_activity_time
            
            if idle_time > settings.CYCLE_IDLE_TIMEOUT:
                action = self._decide_idle_action()
                logger.info(f"[{self.name}] 系统空闲 ({idle_time:.1f}s)，决定动作: {action}")
                
                if action == "sleep":
                    # 仅记录，不触发 S 脑，重置时间
                    self.reset()
                    continue

                payload_content = "系统已空闲一段时间。"
                if action == "exploration":
                    payload_content += " S脑产生了自主探索和学习的欲望。"
                elif action == "connection":
                    payload_content += " S脑产生了与用户建立联结的渴望。"
                else:
                    payload_content += " S脑需自发思考当前状态。"

                event_bus.publish(Event(
                    type="system_heartbeat",
                    source="idle_trigger",
                    payload=SystemHeartbeatPayload(content=payload_content),
                    meta={"idle_action": action}
                ))
                
                self._trigger(f"System Idle Action: {action}")
                # 触发后重置，防止连续触发
                self.reset()
