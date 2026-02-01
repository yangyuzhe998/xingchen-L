
import sys
import os
import time
import threading
from datetime import datetime

# 确保能导入 src 模块
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from core.driver import Driver
from core.navigator import Navigator
from psyche.psyche_core import Psyche
from memory.memory_core import Memory
from core.cycle_manager import CycleManager
from core.bus import event_bus

def run_time_perception_test():
    print("=== XingChen-V Time Perception Test (20 Turns) ===")
    
    # 1. Setup Test Environment
    test_storage = "src/memory/test_time_storage.json"
    test_diary = "src/memory/test_time_diary.md"
    test_vector = "src/memory/test_time_chroma"
    
    # Clean previous artifacts
    if os.path.exists(test_storage): os.remove(test_storage)
    if os.path.exists(test_diary): os.remove(test_diary)
    
    print("[1] Initializing Components...")
    memory = Memory(storage_path=test_storage, vector_db_path=test_vector, diary_path=test_diary)
    psyche = Psyche()
    navigator = Navigator(memory=memory)
    memory.set_navigator(navigator)
    driver = Driver(memory=memory)
    cycle_manager = CycleManager(navigator, psyche)
    
    print("[2] Starting Conversation Loop (Target: 20 turns)...")
    
    # 为了触发多次日记生成，我们需要快速填充 ShortTerm (Max 50)
    # 这里的 20 轮 * 2 (User+Agent) = 40 条消息
    # 我们需要预先填充一些“旧记忆”来模拟之前的对话，以便更快触发压缩
    print("Pre-filling memory to accelerate compaction trigger...")
    for i in range(30):
        memory.add_short_term("user", f"Old message {i}")
        memory.add_short_term("assistant", f"Old reply {i}")
        
    print(f"Memory pre-filled. Current ShortTerm: {len(memory.short_term)}")

    conversations = [
        "你好，现在几点了？", 
        "我们来测试一下你的时间感。",
        "如果我说话很快，你会觉得烦吗？",
        "请记住，时间对人类来说很宝贵。",
        "对 AI 来说，时间意味着什么？",
        "快点回答我。",
        "再快点！",
        "你觉得刚才过了多久？",
        "我们休息一秒钟。",
        "好了，继续测试。",
    ] * 2 # 20 turns
    
    for i, user_input in enumerate(conversations):
        turn = i + 1
        print(f"\n--- Turn {turn}/20 ---")
        
        print(f"[Input] {user_input}")
        
        try:
            response = driver.think(user_input, psyche_state=psyche.state)
            print(f"[Agent] {response}")
        except Exception as e:
            print(f"[Error] Driver failed: {e}")
        
        # 模拟极短的间隔，测试“秒回”反应
        time.sleep(0.5) 
        
        # Check if compaction triggered
        if len(memory.short_term) > 50:
             print("!!! Threshold Reached. Watching for Compaction (and Time Perception)...")
             # Wait a bit for async thread to finish diary writing
             time.sleep(5)
    
    print("\n[3] Verification Phase")
    
    if os.path.exists(test_diary):
        print(f"[Pass] Diary file created: {test_diary}")
        with open(test_diary, 'r', encoding='utf-8') as f:
            print(f"Diary Content Preview:\n{f.read()}")
    else:
        print("[Fail] Diary file NOT found.")

    cycle_manager.running = False
    print("\n=== Test Completed ===")

if __name__ == "__main__":
    run_time_perception_test()
