import threading
import time
import os
import json
from datetime import datetime

from src.core.bus.event_bus import event_bus
from src.schemas.events import BaseEvent as Event
from src.utils.logger import logger
from .triggers.count import MessageCountTrigger
from .triggers.emotion import EmotionTrigger
from .triggers.idle import IdleTrigger
from .triggers.memory import MemoryFullTrigger
from .triggers.knowledge import KnowledgeTrigger

class CycleManager:
    """
    动态周期管理器 (Coordinator)
    职责：协调各个触发器，统一调度 S 脑任务
    """
    def __init__(self, navigator, psyche):
        self.navigator = navigator
        self.psyche = psyche
        self.running = True
        self.start_time = time.time() # [Phase 6.5] 记录启动时间
        
        # 注册触发器
        self.triggers = [
            MessageCountTrigger(self),
            EmotionTrigger(self),
            IdleTrigger(self),
            MemoryFullTrigger(self),
            KnowledgeTrigger(self)
        ]
        
        # 订阅总线
        event_bus.subscribe(self._on_event)
        
        # 启动触发器后台任务
        for t in self.triggers:
            t.start()
            
        # [Phase 6.3] 启动数据库维护任务
        self._start_database_maintenance()
            
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

        # Debug CLI request: 强制触发一次 S 脑分析
        if event.type == "debug_request":
            payload = event.payload_data
            action = payload.get("action")
            if action == "force_s":
                threading.Thread(target=self._handle_force_s, daemon=True).start()
                return

        for t in self.triggers:
            # 这里的 check 是同步的，如果 Trigger 内部逻辑复杂，应自行异步
            t.check(event)

    def _handle_force_s(self):
        """处理 DebugCLI 的 /force_s 请求"""
        try:
            event_bus.publish(Event(
                type="debug_response",
                source="cycle_manager",
                payload={"action": "force_s", "status": "started"},
                meta={},
            ))
            self.trigger_reasoning("debug_force_s")
            event_bus.publish(Event(
                type="debug_response",
                source="cycle_manager",
                payload={"action": "force_s", "status": "done"},
                meta={},
            ))
        except Exception as e:
            logger.error(f"[CycleManager] force_s failed: {e}", exc_info=True)
            event_bus.publish(Event(
                type="debug_response",
                source="cycle_manager",
                payload={"action": "force_s", "status": "error", "error": str(e)},
                meta={},
            ))

    def trigger_reasoning(self, reason):
        """
        [Action] 触发 S 脑深度分析 (R1 Cycle)
        """
        logger.info(f"[CycleManager] ⚡ 触发 S脑分析! 原因: {reason}")
        
        # 1. 重置相关状态 (如计数器、空闲计时器)
        for t in self.triggers:
            if hasattr(t, 'reset'):
                t.reset()
        
        # --- [Phase 2.3] 应用性格漂移 (Bottom-Up) ---
        drift = self._calculate_baseline_drift()
        if drift:
            dims = self.psyche.state["dimensions"]
            for dim, change in drift.items():
                if dim in dims:
                    old_baseline = dims[dim]["baseline"]
                    # 限制在 0.05 - 0.95 之间，保留一点边界
                    dims[dim]["baseline"] = max(0.05, min(0.95, old_baseline + change))
            logger.info(f"[CycleManager] 🌊 情绪累积导致性格漂移: {drift}")

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

    def trigger_internalization(self, reason):
        """
        [Action] 触发 S 脑知识内化 (Knowledge Internalization)
        """
        logger.info(f"[CycleManager] 📚 触发知识内化! 原因: {reason}")
        self.navigator.request_knowledge_internalization()

    def _start_database_maintenance(self):
        """启动定期维护任务：数据库清理 (24h) + 每日快照 (24h) + 增强心跳 (1h) (Phase 6.3/6.5)"""
        def _publish_heartbeat():
            """发布系统心跳事件"""
            uptime_seconds = time.time() - self.start_time
            days, remainder = divmod(int(uptime_seconds), 86400)
            hours, remainder = divmod(remainder, 3600)
            minutes = remainder // 60
            if days > 0:
                uptime_str = f"{days}天 {hours}小时"
            elif hours > 0:
                uptime_str = f"{hours}小时 {minutes}分钟"
            else:
                uptime_str = f"{minutes}分钟"
            
            event_bus.publish(Event(
                type="system_heartbeat",
                source="cycle_manager",
                payload={"content": f"系统运行正常。Uptime: {uptime_str}"},
                meta={
                    "status": "production_ready",
                    "uptime_seconds": int(uptime_seconds),
                    "uptime_str": uptime_str,
                    "memory_stats": self.navigator.memory.knowledge_db.get_stats() if hasattr(self.navigator.memory.knowledge_db, 'get_stats') else {}
                }
            ))

        def _maintenance_loop():
            last_maint_day = None
            
            # [Fix] 启动后立即发送一次心跳，前端不用等 1 小时
            try:
                import time as _t
                _t.sleep(5)  # 等待 5 秒确保 WebApp 启动完成
                _publish_heartbeat()
                logger.info("[CycleManager] 📡 初始心跳已发送。")
            except Exception as e:
                logger.warning(f"[CycleManager] 初始心跳发送失败: {e}")
            
            while self.running:
                try:
                    current_day = datetime.now().strftime('%Y%m%d')
                    
                    # 1. 每日任务：数据库清理 + 每日快照 (24小时执行一次)
                    if last_maint_day != current_day:
                        # 数据库清理
                        retention_days = 30
                        logger.info(f"[CycleManager] 🧹 执行数据库维护：清理 {retention_days} 天前的旧事件...")
                        count = event_bus.cleanup_old_events(days=retention_days)
                        if count > 0:
                            logger.info(f"[CycleManager] 🧹 已从 bus.db 清理 {count} 条过期事件。")

                        # 每日快照
                        telemetry_dir = os.path.join(settings.PROJECT_ROOT, "storage", "telemetry")
                        os.makedirs(telemetry_dir, exist_ok=True)
                        snapshot_path = os.path.join(telemetry_dir, f"snapshot_{current_day}.json")
                        
                        mem_stats = self.navigator.memory.knowledge_db.get_stats() if hasattr(self.navigator.memory.knowledge_db, 'get_stats') else {}
                        snapshot_data = {
                            "timestamp": datetime.now().isoformat(),
                            "psyche": self.psyche.get_raw_state(),
                            "memory_stats": mem_stats
                        }
                        with open(snapshot_path, "w", encoding="utf-8") as f:
                            json.dump(snapshot_data, f, ensure_ascii=False, indent=2)
                        logger.info(f"[CycleManager] 📸 已保存每日演化快照: {snapshot_path}")
                        
                        last_maint_day = current_day

                    # 2. 每小时任务：增强系统心跳 (Phase 6.5)
                    _publish_heartbeat()

                except Exception as e:
                    logger.error(f"[CycleManager] ❌ 维护循环任务失败: {e}")
                
                # 每 1 小时检查一次任务
                time.sleep(3600)

        threading.Thread(target=_maintenance_loop, daemon=True).start()

    def _calculate_baseline_drift(self) -> dict:
        """分析情绪历史，决定是否推动 baseline 漂移 (Phase 2.2)"""
        history = self.psyche.state.get("emotion_history", [])
        if len(history) < 10:
            return {}

        # 取最近 50 条进行统计
        recent = history[-50:]
        emotion_stats = {}
        for record in recent:
            for emo, val in record.get("emotions", {}).items():
                if emo not in emotion_stats:
                    emotion_stats[emo] = []
                emotion_stats[emo].append(val)

        drift = {}
        persistence = 0.02  # 漂移因子，控制变化速度

        # 情绪到 baseline 维度的映射关系
        mapping = {
            "achievement": {"curiosity": +1, "laziness": -1},
            "frustration": {"fear": +1, "curiosity": -0.5},
            "anticipation": {"curiosity": +1},
            "grievance": {"intimacy": -0.5, "fear": +0.3}
        }

        for emo, values in emotion_stats.items():
            avg = sum(values) / len(values)
            if avg > 0.2:  # 阈值：只有持续出现的情绪才会引发性格漂移
                if emo in mapping:
                    for dim, direction in mapping[emo].items():
                        drift[dim] = drift.get(dim, 0) + avg * direction * persistence

        return drift
