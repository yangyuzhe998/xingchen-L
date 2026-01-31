from core.bus import event_bus, Event
from core.navigator import Navigator
from psyche.psyche_core import Psyche
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
        
        # 启动监控线程
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

        # 启动 Moltbook 心跳线程 (每 4 小时检查一次，这里演示改为每 60s)
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()
        
        print("[CycleManager] 动态周期监控 & 社交心跳已启动。")

    def _heartbeat_loop(self):
        """Moltbook 心跳循环"""
        while self.running:
            try:
                # 检查 Moltbook 状态
                moltbook_client.check_heartbeat()
                # 心跳间隔设为 1 小时 (3600s)
                time.sleep(3600) 
            except Exception as e:
                print(f"[CycleManager] Heartbeat Error: {e}")
                time.sleep(60)

    def _monitor_loop(self):
        """
        监控循环：虽然 SQLite 不支持 Push，但我们可以轮询 ID 变化或者由 Driver 主动 notify
        这里为了简单，我们采用“每次 Driver 回复后”检查一次
        在实际生产中，应该是 EventBus 推送过来
        """
        last_event_id = 0
        
        while self.running:
            try:
                # 获取最新事件
                events = event_bus.get_events(limit=10, start_time=self.last_analysis_time)
                if not events:
                    time.sleep(1)
                    continue

                for event in events:
                    if event.id <= last_event_id:
                        continue
                    last_event_id = event.id
                    
                    if event.type == "driver_response":
                        self.message_count += 1
                        self._check_triggers(event)
                
                time.sleep(0.5)
            except Exception as e:
                print(f"[CycleManager] Monitor Error: {e}")
                time.sleep(2)

    def _check_triggers(self, event):
        """检查是否满足触发条件"""
        trigger_reason = None
        
        # 1. 计数器触发 (比如每 5 轮对话触发一次，方便演示)
        if self.message_count >= 5:
            trigger_reason = "Message Count Limit (5)"
        
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
