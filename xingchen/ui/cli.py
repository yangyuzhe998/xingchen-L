import sys
import threading
import time
import json
from datetime import datetime
from typing import Dict, Any, Callable

from xingchen.core.event_bus import event_bus
from xingchen.schemas.events import BaseEvent as Event
from xingchen.utils.logger import logger
from xingchen.interfaces.ui_interface import UserInterface


class DebugCLI(UserInterface):
    """
    调试专用 CLI (Debug Command Line Interface)
    特点：
    1. 同步阻塞输入 (input)
    2. 实时打印 EventBus 上的所有重要事件
    3. 支持调试指令 (以 / 开头)
    """
    def __init__(self):
        self.running = True
        self.input_handler = None
        # 订阅所有事件
        event_bus.subscribe(self._event_listener)
        logger.info("[CLI] Debug CLI 初始化完成。")

    def set_input_handler(self, handler: Callable[[str], None]):
        self.input_handler = handler

    def display_message(self, role: str, content: str, meta: Dict[str, Any] = None):
        """Debug 模式下，主要依靠 EventBus 打印，此处作为回调备份"""
        pass

    def update_status(self, status: str, details: Dict[str, Any] = None):
        pass

    def _event_listener(self, event: Event):
        """监听并实时打印所有事件"""
        try:
            timestamp = datetime.fromtimestamp(event.timestamp).strftime('%H:%M:%S.%f')[:-3]

            # A. 特殊处理 debug_response
            if event.type == "debug_response":
                payload = event.payload_data
                action = payload.get("action")
                print(f"\n{timestamp} === [Debug Response] Source: {event.source}")

                if action == "dump_short_term":
                    data = payload.get("data", [])
                    print(f"ShortTerm Count: {len(data)}")
                    for i, item in enumerate(data[-10:]): # 仅展示最近 10 条
                        role = item.get("role", "?")
                        content = item.get("content", "")
                        display = content if len(content) <= 100 else content[:100] + "..."
                        print(f"  {i+1:02d}. [{role}] {display}")
                    return

                print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
                return

            # B. 常规事件映射
            prefix_map = {
                "user_input": ">>> [User Input]",
                "driver_response": "<<< [Driver Response]",
                "navigator_suggestion": "*** [S-Brain Suggestion]",
                "proactive_instruction": "!!! [S-Brain Proactive]",
                "system_heartbeat": "--- [System Heartbeat]",
                "psyche_update": "~~~ [Psyche Update]",
                "system_notification": "📢 [System Notice]"
            }
            
            prefix = prefix_map.get(event.type, f"--- [{event.type}]")
            print(f"\n{timestamp} {prefix} Source: {event.source}")

            payload = event.payload_data
            if event.type in ["user_input", "driver_response", "navigator_suggestion", "system_heartbeat"]:
                content = payload.get("content", "")
                if content:
                    print(f"Content: {content}")
            
            if event.type == "psyche_update":
                if "narrative" in payload:
                    print(f"Narrative: {payload['narrative']}")
                if event.meta and "dimensions" in event.meta:
                    dims = event.meta["dimensions"]
                    dim_str = " | ".join([f"{k}: {v:.2f}" for k, v in dims.items()])
                    print(f"Dimensions: {dim_str}")

            if event.type == "driver_response" and event.meta.get("inner_voice"):
                print(f"Inner Voice: 💭 {event.meta['inner_voice']}")

        except Exception as e:
            pass

    def run(self):
        """启动 CLI 循环"""
        print("\n" + "="*50)
        print("   星辰-V (XingChen-V) 生产级调试终端已上线")
        print("   输入消息开始对话，输入 /help 查看指令")
        print("="*50 + "\n")
        
        while self.running:
            try:
                # 阻塞获取输入
                user_input = input("\n[User]: ").strip()
                if not user_input:
                    continue

                # 1. 处理系统级指令
                if user_input.startswith("/"):
                    self._handle_command(user_input)
                    continue

                # 2. 调用处理器 (Driver.think)
                if self.input_handler:
                    self.input_handler(user_input)
                else:
                    print("[System Error]: No input handler registered.")
                    
            except KeyboardInterrupt:
                print("\n[System]: 正在退出调试终端...")
                self.running = False
            except Exception as e:
                print(f"\n[System Error]: {e}")
                logger.error(f"[CLI] Run loop error: {e}", exc_info=True)

    def _handle_command(self, cmd: str):
        """处理内部调试指令"""
        parts = cmd.split()
        base = parts[0].lower()

        if base == "/help":
            print("\n[可用指令]:")
            print("  /help            - 显示帮助")
            print("  /status          - 查看系统资源与统计")
            print("  /dump_st         - 导出最近 30 条短期记忆")
            print("  /force_s         - 强制触发一次 S 脑周期分析")
            print("  /exit            - 退出程序")
        
        elif base == "/status":
            print("\n[System Status]:")
            print(f"  Local Time: {datetime.now().isoformat()}")
            # 发送探测事件，让其他组件汇报状态
            event_bus.publish(Event(type="debug_request", source="cli", payload={"action": "get_status"}))

        elif base == "/dump_st":
            event_bus.publish(Event(type="debug_request", source="cli", payload={"action": "dump_short_term"}))

        elif base == "/force_s":
            event_bus.publish(Event(type="debug_request", source="cli", payload={"action": "force_s"}))

        elif base == "/exit":
            self.running = False
        else:
            print(f"[System]: 未知指令 '{base}'。输入 /help 查看列表。")
