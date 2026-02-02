import sys
import os
import time
sys.path.append(os.getcwd())

from src.core.navigator import Navigator
from src.memory.memory_core import Memory
from src.core.bus import event_bus, Event

def force_generate_diary():
    print("🚀 Forcing AI Diary Generation...")
    
    # 1. Init
    memory = Memory()
    navigator = Navigator(memory=memory)
    memory.set_navigator(navigator)
    
    # 2. Mock some events if bus is empty (optional, but good for testing context)
    # If the comprehensive test just ran, the bus might still have events if persistence is enabled.
    # But let's add some fresh mock events to be sure.
    print("📝 Injecting mock events...")
    event_bus.publish(Event("user_input", "user", {"content": "今天天气真不错，但我心情不好。"}, {}))
    event_bus.publish(Event("driver_response", "driver", {"content": "哼，心情不好关我什么事...不过你要是想哭，借你个肩膀也不是不行。" }, {}))
    event_bus.publish(Event("user_input", "user", {"content": "谢谢你，星辰。"}, {}))
    
    # 3. Call generate_diary directly
    print("⏳ Calling navigator.generate_diary()...")
    response = navigator.generate_diary()
    
    print("\n✅ Diary Generation Result:")
    print(response)
    
    # 4. Check file
    diary_path = "src/memory/diary.md"
    if os.path.exists(diary_path):
        print(f"\n📂 Diary file exists at: {diary_path}")
        with open(diary_path, "r", encoding="utf-8") as f:
            print("--- File Content Preview ---")
            print(f.read()[-500:]) # Show last 500 chars
            print("--------------------------")
    else:
        print(f"\n❌ Diary file NOT found at: {diary_path}")

if __name__ == "__main__":
    force_generate_diary()
