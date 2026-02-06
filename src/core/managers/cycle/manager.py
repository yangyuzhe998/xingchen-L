from src.core.bus.event_bus import event_bus, Event
from src.utils.logger import logger
from .triggers.count import MessageCountTrigger
from .triggers.emotion import EmotionTrigger
from .triggers.idle import IdleTrigger
from .triggers.memory import MemoryFullTrigger

class CycleManager:
    """
    动态周期管理器 (Coordinator)
    职责：协调各个触发器，统一调度 S 脑任务
    """
    def __init__(self, navigator, psyche):
        self.navigator = navigator
        self.psyche = psyche
        self.running = True
        
        # 注册触发器
        self.triggers = [
            MessageCountTrigger(self),
            EmotionTrigger(self),
            IdleTrigger(self),
            MemoryFullTrigger(self)
        ]
        
        # 订阅总线
        event_bus.subscribe(self._on_event)
        
        # 启动触发器后台任务
        for t in self.triggers:
            t.start()
            
        logger.info("[CycleManager] 动态周期监控 (v4.0 Triggers) 已启动。")

    def stop(self):
        """停止管理器和所有触发器"""
        self.running = False
        for t in self.triggers:
            t.stop()
        logger.info("[CycleManager] 已停止。")

    def _on_event(self, event):
        """事件分发"""
        if not self.running:
            return
            
        for t in self.triggers:
            # 这里的 check 是同步的，如果 Trigger 内部逻辑复杂，应自行异步
            t.check(event)

    def trigger_reasoning(self, reason):
        """
        [Action] 触发 S 脑深度分析 (R1 Cycle)
        """
        logger.info(f"[CycleManager] ⚡ 触发 S脑分析! 原因: {reason}")
        
        # 1. 重置相关状态 (如计数器、空闲计时器)
        for t in self.triggers:
            if hasattr(t, 'reset'):
                t.reset()
        
        # 2. 调用 S 脑 (R1 模式)
        suggestion, delta, proactive_instruction = self.navigator.analyze_cycle()
        
        # 3. 更新 Psyche
        if delta:
            self.psyche.update_state(delta)
            
        # 4. 发布 Suggestion
        if suggestion:
            event_bus.publish(Event(
                type="navigator_suggestion",
                source="navigator",
                payload={"content": suggestion},
                meta={"trigger": "cycle_end"}
            ))
            logger.info(f"[CycleManager] S脑建议已发布: {suggestion}")

        # 5. 处理主动干预指令
        if proactive_instruction:
            logger.info(f"[CycleManager] 收到主动干预指令: {proactive_instruction}")
            event_bus.publish(Event(
                type="proactive_instruction",
                source="navigator",
                payload={"content": proactive_instruction},
                meta={"trigger": "cycle_end"}
            ))

    def trigger_compression(self, reason):
        """
        [Action] 触发 S 脑记忆压缩 (Diary Generation)
        """
        logger.info(f"[CycleManager] 📦 触发记忆压缩! 原因: {reason}")
        self.navigator.request_diary_generation()
