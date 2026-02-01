from core.bus import event_bus, Event
from core.navigator import Navigator
from psyche.psyche_core import Psyche
from config.settings import settings
import threading
import time
import sys
import os

# 动态添加路径以导入 social 模块 (临时方案)
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__))))
from social.moltbook_client import moltbook_client

class CycleManager:
    """
    动态周期触发器
    负责监控总线事件，判断何时触发 S脑 (Navigator) 的深度分析。
    触发条件：
    1. 对话轮数阈值 (TOKEN/Count)
    2. 情绪剧烈波动 (Emotion Spike)
    3. 关键指令 (Key Instruction)
    """
    def __init__(self, navigator: Navigator, psyche: Psyche):
        self.navigator = navigator
        self.psyche = psyche
        self.message_count = 0
        self.last_analysis_time = time.time()
        self.running = True
        
        # 订阅总线事件 (Observer Mode)
        event_bus.subscribe(self._on_event)
        
        # 启动 Moltbook 心跳线程
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()
        
        print("[CycleManager] 动态周期监控(Observer) & 社交心跳已启动。")

    def _on_event(self, event):
        """事件回调函数"""
        if not self.running:
            return
            
        if event.type == "driver_response":
            self.message_count += 1
            self._check_triggers(event)

    def _heartbeat_loop(self):
        """Moltbook 心跳循环"""
        if not moltbook_client:
            return

        while self.running:
            try:
                # 检查 Moltbook 状态
                moltbook_client.check_heartbeat()
                # 心跳间隔设为 settings 中配置的值
                time.sleep(settings.HEARTBEAT_INTERVAL) 
            except Exception as e:
                print(f"[CycleManager] Heartbeat Error: {e}")
                time.sleep(60)

    # 废弃：不再需要轮询循环
    # def _monitor_loop(self):
    #     ...

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
        suggestion, delta = self.navigator.analyze_cycle()
        
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
