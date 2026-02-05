from ..bus.event_bus import event_bus, Event
# from ..navigator.engine import Navigator # Circular import fix
from ...psyche import PsycheEngine
from ...config.settings.settings import settings
import threading
import time
import sys
import os

# from ...social.moltbook_client import moltbook_client

class CycleManager:
    """
    动态周期触发器
    负责监控总线事件，判断何时触发 S脑 (Navigator) 的深度分析。
    触发条件：
    1. 对话轮数阈值 (TOKEN/Count)
    2. 情绪剧烈波动 (Emotion Spike)
    3. 关键指令 (Key Instruction)
    """
    def __init__(self, navigator, psyche: PsycheEngine):
        self.navigator = navigator
        self.psyche = psyche

        self.message_count = 0
        self.last_analysis_time = time.time()
        self.running = True
        
        # 订阅总线事件 (Observer Mode)
        event_bus.subscribe(self._on_event)
        
        # 启动 Moltbook 心跳线程 (已移除)
        # self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        # self.heartbeat_thread.start()
        
        # 启动空闲监控线程
        self.idle_monitor_thread = threading.Thread(target=self._idle_monitor_loop, daemon=True)
        self.idle_monitor_thread.start()
        
        print("[CycleManager] 动态周期监控(Observer) 已启动。")

    def _idle_monitor_loop(self):
        """空闲监控循环：如果太久没有分析，强制触发一次 (避免 S脑 饿死)"""
        IDLE_TIMEOUT = settings.CYCLE_IDLE_TIMEOUT
        while self.running:
            time.sleep(10)
            if time.time() - self.last_analysis_time > IDLE_TIMEOUT:
                print(f"[CycleManager] 系统空闲超时 ({IDLE_TIMEOUT}s)，强制触发 S脑分析...")
                # 注入心跳事件，确保 S脑 有米下锅
                event_bus.publish(Event(
                    type="system_heartbeat",
                    source="cycle_manager",
                    payload={"content": "系统已空闲一段时间。S脑需自发思考当前状态或决定是否进行社交活动。"},
                    meta={}
                ))
                self._trigger_s_brain()

    def _on_event(self, event):
        """事件回调函数"""
        if not self.running:
            return
            
        if event.type == "driver_response":
            self.message_count += 1
            self._check_triggers(event)

    # def _heartbeat_loop(self):
    #     """Moltbook 心跳循环 (已移除)"""
    #     if not moltbook_client:
    #         return
    #
    #     while self.running:
    #         try:
    #             # 检查 Moltbook 状态
    #             moltbook_client.check_heartbeat()
    #             # 心跳间隔设为 settings 中配置的值
    #             time.sleep(settings.HEARTBEAT_INTERVAL) 
    #         except Exception as e:
    #             print(f"[CycleManager] Heartbeat Error: {e}")
    #             time.sleep(60)

    def stop(self):
        """优雅停止所有守护线程"""
        self.running = False
        print("[CycleManager] 正在停止监控线程...")
        # 等待线程结束（可选，这里简单设置标志位）


    def _check_triggers(self, event):
        """检查是否满足触发条件"""
        trigger_reason = None
        
        # 1. 计数器触发
        if self.message_count >= settings.CYCLE_TRIGGER_COUNT:
            trigger_reason = f"Message Count Limit ({settings.CYCLE_TRIGGER_COUNT})"
        
        # 2. 情绪触发
        meta = event.meta
        if meta and "user_emotion_detect" in meta:
            emotion = meta["user_emotion_detect"]
            if emotion in ["angry", "sad", "fear"]:
                trigger_reason = f"Negative Emotion Detected: {emotion}"
        
        if trigger_reason:
            print(f"\n[CycleManager] 触发 S脑分析! 原因: {trigger_reason}")
            self._trigger_s_brain()

    def _trigger_s_brain(self):
        """执行 S脑 分析周期"""
        # 1. 重置计数器
        self.message_count = 0
        self.last_analysis_time = time.time()
        
        # 2. 调用 S脑 (R1 模式)
        # 注意：这里我们不再传具体的 input，而是让 S脑自己去 Bus 里捞最近的一个周期
        # 这里的实现需要 Navigator 支持“无参分析”或“基于 Bus 分析”
        suggestion, delta, proactive_instruction = self.navigator.analyze_cycle()
        
        # 3. 更新 Psyche
        if delta:
            self.psyche.update_state(delta)
            
        # 4. 将 Suggestion 发布回总线，供 Driver 下次读取
        if suggestion:
            event_bus.publish(Event(
                type="navigator_suggestion",
                source="navigator",
                payload={"content": suggestion},
                meta={"trigger": "cycle_end"}
            ))
            print(f"[CycleManager] S脑建议已发布: {suggestion}")

        # 5. 处理主动干预指令
        if proactive_instruction:
            print(f"[CycleManager] 收到主动干预指令: {proactive_instruction}")
            event_bus.publish(Event(
                type="proactive_instruction",
                source="navigator",
                payload={"content": proactive_instruction},
                meta={"trigger": "cycle_end"}
            ))
