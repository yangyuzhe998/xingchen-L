import sys
import os
import time
import threading
from datetime import datetime

# 确保项目根目录在 sys.path 中
sys.path.append(os.getcwd())

from src.core.driver import Driver
from src.core.navigator import Navigator
from src.psyche.psyche_core import Psyche
from src.memory.memory_core import Memory
from src.core.cycle_manager import CycleManager
from src.core.bus import event_bus
from src.core.library_manager import library_manager
from src.skills.loader import skill_loader

# 模拟用户输入序列 (20轮)
SIMULATED_DIALOGUE = [
    "你好，星辰。初次见面。",
    "现在几点了？",  # 测试 Time Tool
    "帮我算一下 3.14 * 50 * 50 等于多少？", # 测试 Calculate Tool
    "你知道怎么查北京的天气吗？", # 测试 Skill Search
    "那请帮我看看上海的天气怎么样？", # 测试 Skill Usage (如果它决定用 shell)
    "我今天心情有点低落，工作很不顺。", # 测试 情绪感知 (Sad)
    "有没有什么办法能让我开心点？", # 延续对话
    "听说你会写代码，是真的吗？", # 测试 元认知
    "记住，我最喜欢的颜色是星空蓝。", # 测试 长期记忆写入
    "刚刚过了多久？我感觉像过了很久。", # 测试 客观时间感知
    "你还记得我喜欢什么颜色吗？", # 测试 长期记忆读取
    "我觉得你刚才的回答有点敷衍，笨蛋。", # 测试 情绪感知 (Angry/Tsundere trigger)
    "对不起，我不是故意骂你的。", # 测试 情绪恢复
    "列出当前目录下的文件看看。", # 测试 Shell Command (Dir)
    "你觉得人工智能未来会统治人类吗？", # 测试 S脑 深度思考
    "给我们这段对话写个简短的总结吧。", # 测试 总结能力
    "我累了，想休息一会儿。",
    "你也会休息吗？",
    "再见啦，星辰。",
    "（沉默）" # 结束
]

def run_comprehensive_test():
    print("🚀 [TEST] Starting Comprehensive Real-world Test (20 Rounds)...")
    print(f"📂 Working Directory: {os.getcwd()}")
    
    # 1. 初始化基础设施
    print("\n--- Phase 1: Initialization ---")
    skill_loader.scan_and_load()
    library_manager.scan_and_index() # 确保技能库是最新的
    
    memory = Memory()
    psyche = Psyche()
    navigator = Navigator(memory=memory)
    memory.set_navigator(navigator)
    driver = Driver(memory=memory)
    
    # 启动 CycleManager (作为守护线程)
    cycle_manager = CycleManager(navigator, psyche)
    
    # 2. 开始对话循环
    target_rounds = 60
    print(f"\n--- Phase 2: Dialogue Loop ({target_rounds} Rounds High-Pressure Test) ---")
    
    # 扩展对话列表以满足 60 轮需求 (循环使用)
    extended_dialogue = (SIMULATED_DIALOGUE * 4)[:target_rounds]
    
    last_suggestion = ""
    start_time = time.time()
    
    for i, user_input in enumerate(extended_dialogue):
        round_num = i + 1
        print(f"\n[Round {round_num}/{target_rounds}] --------------------------------------------------")
        print(f"👤 User: {user_input}")
        
        # 模拟思考时间 (减少 sleep 以加快高压测试速度)
        time.sleep(0.5) 
        
        # 检查 S脑 建议
        suggestions = event_bus.get_events(limit=1, event_type="navigator_suggestion")
        if suggestions:
            last_suggestion = suggestions[-1].payload.get("content", "")
            # print(f"💡 [Subconscious/Suggestion]: {last_suggestion}")
        
        # 获取 Psyche 状态
        psyche_state = psyche.state
        # print(f"🧠 [Psyche State]: Curiosity={psyche_state.curiosity:.2f}...")
        
        # F脑 思考与行动
        try:
            response = driver.think(user_input, psyche_state=psyche_state, suggestion=last_suggestion)
            print(f"🤖 Agent: {response}")
        except Exception as e:
            print(f"❌ [Error] Driver failed: {e}")
        
        # 模拟 S脑 强制触发检查
        # 注意：真实 CycleManager 是异步的，这里我们不刻意 sleep 等待，模拟高频输入压力
        # 仅在关键节点稍微停顿观察
        if round_num % 10 == 0:
            print(f"--- [Checkpoint {round_num}] Check memory compression status ---")
            time.sleep(2) 

    total_time = time.time() - start_time
    print(f"\n--- Phase 3: Test Summary ---")
    print(f"✅ Completed {target_rounds} rounds in {total_time:.2f} seconds.")
    print("Please check the logs above for:")
    print("1. Tool Usage (Calculate, Shell, Skill Search)")
    print("2. Memory Persistence (Did it remember the color?)")
    print("3. S-Brain Triggers (Did Navigator analyze the cycle?)")
    
    # 停止 CycleManager
    cycle_manager.running = False
    print("🛑 Test Finished.")

if __name__ == "__main__":
    run_comprehensive_test()
