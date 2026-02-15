
import sys
import threading
import time
import json
from datetime import datetime

from src.core.driver.engine import Driver
from src.core.navigator.core import Navigator
from src.psyche import psyche_engine
from src.memory.memory_core import Memory
from src.core.managers import CycleManager
from src.core.bus.event_bus import event_bus
from src.schemas.events import BaseEvent as Event
from src.utils.logger import logger
from src.interfaces.ui_interface import UserInterface

class DebugCLI(UserInterface):
    """
    调试专用 CLI
    特点：
    1. 同步阻塞输入 (input)
    2. 实时打印 EventBus 上的所有事件
    3. 支持调试指令
    """
    def __init__(self):
        self.running = True
        self.input_handler = None

    def set_input_handler(self, handler):
        self.input_handler = handler

    def display_message(self, role: str, content: str, meta: dict = None):
        # Debug 模式下，主要依靠 EventBus 打印，这里只打印最终结果
        if role == "assistant":
            print(f"\n[Agent]: {content}")
        elif role == "system":
            print(f"\n[System]: {content}")

    def update_status(self, status: str, details: dict = None):
        pass # Debug 模式不需要状态栏

    def _event_listener(self, event: Event):
        """
        监听并打印所有事件
        """
        try:
            timestamp = datetime.fromtimestamp(event.timestamp).strftime('%H:%M:%S.%f')[:-3]

            # 特殊处理 debug_response：更友好输出
            if event.type == "debug_response":
                payload = event.payload_data
                action = payload.get("action")
                print(f"\n{timestamp} === [Debug Response] Source: {event.source}")

                if action == "dump_short_term":
                    data = payload.get("data", [])
                    print(f"ShortTerm Count: {len(data)}")
                    for i, item in enumerate(data[-30:]):
                        role = item.get("role", "?")
                        content = item.get("content", "")
                        ts = item.get("timestamp", "")
                        if ts:
                            try:
                                ts_str = str(ts)[:19]
                            except:
                                ts_str = ""
                        else:
                            ts_str = ""
                        # 截断输出避免刷屏
                        display = content if len(content) <= 200 else content[:200] + "..."
                        print(f"  {i+1:02d}. [{role}] {display}")
                    return

                print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
                if event.meta:
                    print(f"Meta: {json.dumps(event.meta, indent=2, ensure_ascii=False)}")
                return

            # 其他事件：默认格式
            prefix = ""
            if event.type == "user_input":
                prefix = ">>> [User Input]"
            elif event.type == "driver_response":
                prefix = "<<< [Driver Response]"
            elif event.type == "navigator_suggestion":
                prefix = "*** [S-Brain Suggestion]"
            elif event.type == "memory_write":
                prefix = "=== [Memory Write]"
            elif event.type == "psyche_update":
                prefix = "~~~ [Psyche Update]"
            else:
                prefix = f"--- [{event.type}]"

            log_line = f"\n{timestamp} {prefix} Source: {event.source}"
            print(log_line)

            payload = event.payload_data
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except:
                    pass

            print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")

            if event.meta:
                print(f"Meta: {json.dumps(event.meta, indent=2, ensure_ascii=False)}")

        except Exception as e:
            print(f"[DebugCLI] Event Print Error: {e}")

    def run(self):
        logger.info("启动 Debug CLI 模式...")
        print("==================================================")
        print("   XingChen-V Debug Console")
        print("   - 监听所有 EventBus 事件")
        print("   - 输入 '/help' 查看调试指令")
        print("==================================================")

        # 1. 启动事件监听线程
        event_bus.subscribe(self._event_listener)

        # 2. 主循环
        while self.running:
            try:
                # 阻塞等待输入
                user_input = input("\n(Debug) User: ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ['exit', 'quit']:
                    self.running = False
                    break

                # 处理调试指令
                if user_input.startswith("/"):
                    self._handle_debug_command(user_input)
                    continue

                # 正常输入处理
                if self.input_handler:
                    self.input_handler(user_input)

            except KeyboardInterrupt:
                self.running = False
                print("\n[DebugCLI] Interrupted.")
                break
            except Exception as e:
                logger.error(f"Debug Loop Error: {e}", exc_info=True)

    def _handle_debug_command(self, cmd: str):
        print(f"[Debug] Executing command: {cmd}")

        if cmd == "/help":
            print("Available Commands:")
            print("  /dump_memory  - 请求当前短期记忆快照")
            print("  /psyche       - 打印当前心智状态")
            print("  /force_s      - 强制触发 S 脑思考")

        elif cmd == "/psyche":
            try:
                state = psyche_engine.get_raw_state()
            except Exception:
                state = getattr(psyche_engine, "state", {})
            print(json.dumps(state, indent=2, ensure_ascii=False))

        elif cmd == "/dump_memory":
            event_bus.publish(Event(
                type="debug_request",
                source="debug_cli",
                payload={"action": "dump_short_term"},
                meta={},
            ))

        elif cmd == "/force_s":
            event_bus.publish(Event(
                type="debug_request",
                source="debug_cli",
                payload={"action": "force_s"},
                meta={},
            ))

        else:
            print("Unknown debug command. Use /help to list commands.")


# 简单的启动器 (如果直接运行此文件)
if __name__ == "__main__":
    # 初始化组件
    memory = Memory()
    psyche = psyche_engine
    navigator = Navigator(memory=memory)
    memory.set_navigator(navigator)
    driver = Driver(memory=memory)
    cycle_manager = CycleManager(navigator, psyche)

    # 启动 UI
    app = DebugCLI()

    def handler(content):
        psyche_state = psyche.state
        driver.think(content, psyche_state=psyche_state)

    app.set_input_handler(handler)

    try:
        app.run()
    finally:
        cycle_manager.running = False
        print("Debug Session Ended.")
