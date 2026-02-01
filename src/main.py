import sys
import os

# 移除硬编码的 sys.path.append，假设通过 python -m src.main 或设置 PYTHONPATH 运行
# sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.driver import Driver
from core.navigator import Navigator
from psyche.psyche_core import Psyche
from memory.memory_core import Memory
from core.cycle_manager import CycleManager
from core.bus import event_bus

def main():
    print("XingChen-V 系统启动中 (Async/R1 Mode)...")
    
    # 初始化组件
    memory = Memory()
    psyche = Psyche()
    navigator = Navigator(memory=memory)
    
    # 关键：注入 Navigator 到 Memory，启用自动压缩
    memory.set_navigator(navigator)
    
    driver = Driver(memory=memory)
    
    # 启动周期管理器 (后台线程)
    cycle_manager = CycleManager(navigator, psyche)
    
    print("\n系统就绪。输入 'exit' 退出。")
    print("--------------------------------------------------")

    last_suggestion = ""

    while True:
        try:
            user_input = input("User: ").strip()
            if user_input.lower() in ['exit', 'quit']:
                cycle_manager.running = False
                print("系统关闭。再见。")
                break
            
            if not user_input:
                continue

            # 检查是否有新的 S脑建议 (来自总线)
            # 在真实异步场景下，Driver 会在一个独立的循环中检查，这里简化为每轮对话前检查一次
            suggestions = event_bus.get_events(limit=1, event_type="navigator_suggestion")
            if suggestions:
                # 获取最新的一条建议
                last_suggestion = suggestions[-1].payload.get("content", "")
                # print(f"[Main] 收到 S脑异步建议: {last_suggestion}")

            # 获取当前心智状态 (注意：Psyche 的更新现在由 CycleManager 异步控制)
            psyche_state = psyche.state
            
            # F脑 (Driver) 独立思考并行动
            # 它不再等待 S脑的实时分析，而是依赖当前的“潜意识”(last_suggestion)
            response = driver.think(user_input, psyche_state=psyche_state, suggestion=last_suggestion)
            
            print(f"Agent: {response}")
            
        except KeyboardInterrupt:
            cycle_manager.running = False
            print("\n强制中断。")
            break
        except Exception as e:
            print(f"发生错误: {e}")
            cycle_manager.running = False

if __name__ == "__main__":
    main()
