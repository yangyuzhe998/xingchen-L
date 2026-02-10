
import os
import sys
import time
import json
from datetime import datetime

# 添加项目根目录到 sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.driver.engine import Driver
from src.memory.memory_core import Memory
from src.memory.storage.knowledge_db import knowledge_db
from src.memory.storage.topic_manager import topic_manager
from src.core.bus.event_bus import event_bus

def print_monitor(title, content):
    """ASCII 风格监控器"""
    print(f"\n[MONITOR: {title}]")
    print("-" * 40)
    print(content)
    print("-" * 40)

def show_detailed_memory():
    """展示详细的指纹与权重变化"""
    recent = topic_manager.get_recent_fragments(limit=3)
    if not recent:
        return "Memory is empty."
    
    report = ""
    for r in recent:
        m = r['metadata']
        report += (
            f"Content: {r['document'][:30]}...\n"
            f"Fingerprint: {m.get('fingerprint', 'N/A')}\n"
            f"Topic/Task: {m.get('topic_id')}/{m.get('task_id')}\n"
            f"Stats: Weight={m.get('weight', 1.0):.2f}, Mentions={m.get('mention_count', 1)}\n"
            f"Active: {m.get('last_activated')}\n"
            f"{'.' * 20}\n"
        )
    return report

def simulate_real_conversation():
    print("--- REAL ENVIRONMENT SIMULATION START ---")
    
    # 强制清理之前的残余 (仅用于演示纯净启动)
    # topic_manager.clear_all() 
    
    memory = Memory()
    driver = Driver(memory=memory)
    
    # 订阅总线以捕获内心独白
    last_event_meta = {}
    def on_event(event):
        nonlocal last_event_meta
        if event.type == "driver_response":
            last_event_meta = event.meta

    event_bus.subscribe(on_event)

    # 第一轮：初步建立印象
    print("\n>>> Scenario 1: Initial Introduction")
    topic_id = topic_manager.create_topic("User_Profile", "Information about the user")
    task_id = topic_manager.create_task(topic_id, "Identity", "First meeting")
    
    user_msg_1 = "Hi, I am Claude. I am an AI researcher who loves quiet environments."
    print(f"User: {user_msg_1}")
    
    # 真实 LLM 调用
    reply_1 = driver.think(user_msg_1)
    # 手动内化一个片段用于演示权重变化逻辑 (现实中由 S脑 异步完成，这里同步演示)
    topic_manager.add_fragment("User loves quiet environments", topic_id=topic_id, task_id=task_id, category="preference")
    
    print(f"Assistant: {reply_1}")
    print_monitor("Inner Thoughts & Emotions", 
                  f"Voice: {last_event_meta.get('inner_voice', 'N/A')}\n"
                  f"Emotion: {last_event_meta.get('user_emotion_detect', 'N/A')}")
    
    # 第二轮：强化印象 (同 Task 下重复)
    print("\n>>> Scenario 2: Reinforcing Impression")
    time.sleep(2)
    user_msg_2 = "As I said before, a quiet space is very important for my AI work."
    print(f"User: {user_msg_2}")
    reply_2 = driver.think(user_msg_2)
    
    # 再次存入相同内容 (同 Task)
    topic_manager.add_fragment("User loves quiet environments", topic_id=topic_id, task_id=task_id, category="preference")
    
    print(f"Assistant: {reply_2}")
    print_monitor("Memory Evolution (Reinforced)", show_detailed_memory())

    # 第三轮：场景隔离测试 (不同 Task)
    print("\n>>> Scenario 3: Contextual Isolation (Apple Paradox Test)")
    task_2 = topic_manager.create_task(topic_id, "Coffee_Shop", "Noisy environment test")
    user_msg_3 = "The coffee shop is loud, but I still prefer a quiet place to work."
    print(f"User: {user_msg_3}")
    reply_3 = driver.think(user_msg_3)
    
    # 存入相同内容但不同 Task
    topic_manager.add_fragment("User loves quiet environments", topic_id=topic_id, task_id=task_2, category="preference")
    
    print(f"Assistant: {reply_3}")
    print_monitor("Memory Evolution (Isolated)", show_detailed_memory())

    print("\n--- SIMULATION END ---")
    print("Check the 'Fingerprint' and 'Weight' above to see her changes.")

if __name__ == "__main__":
    try:
        simulate_real_conversation()
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
