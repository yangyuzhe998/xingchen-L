import sys
import os

# 确保 src 在 python 路径中
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.driver import Driver
from core.navigator import Navigator
from psyche.psyche_core import Psyche
from memory.memory_core import Memory

def main():
    print("XingChen-V 系统启动中...")
    
    # 初始化组件 (共享记忆)
    memory = Memory()
    psyche = Psyche()
    navigator = Navigator(memory=memory)
    driver = Driver(memory=memory)
    
    print("\n系统就绪。输入 'exit' 退出。")
    print("--------------------------------------------------")

    while True:
        try:
            user_input = input("User: ").strip()
            if user_input.lower() in ['exit', 'quit']:
                print("系统关闭。再见。")
                break
            
            if not user_input:
                continue

            # 1. S脑 (Navigator) 先行分析
            # S脑基于共享记忆和当前输入进行分析，给出建议和心智评分
            suggestion, delta = navigator.analyze(user_input)
            
            if suggestion:
                print(f"[Main] S脑建议: {suggestion}")
            
            # 2. 心智模块 (Psyche) 更新状态
            if delta:
                psyche.update_state(delta)
            
            # 获取最新的 Prompt 修饰词
            prompt_mod = psyche.get_prompt_modifier()
            
            # 3. F脑 (Driver) 后置执行
            # F脑结合 S脑建议 和 最新心智状态 进行回复
            response = driver.think(user_input, psyche_modifier=prompt_mod, suggestion=suggestion)
            print(f"Agent: {response}")
            
        except KeyboardInterrupt:
            print("\n强制中断。")
            break
        except Exception as e:
            print(f"发生错误: {e}")

if __name__ == "__main__":
    main()
