import sys
import os
import time

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.navigator.engine import Navigator
from src.core.bus.event_bus import event_bus, Event
from src.memory.memory_core import Memory

def debug_navigator_cycle():
    print("=== Debugging Navigator Cycle ===")
    
    # 1. Initialize Components
    memory = Memory()
    nav = Navigator(name="DebugNavigator", memory=memory)
    
    # 2. Check Event Bus
    # We expect events to be there from previous runs (bus.db persistence)
    print("\n[Debug] Checking Event Bus...")
    events = event_bus.get_latest_cycle(limit=50)
    print(f"[Debug] Found {len(events)} events in the bus.")
    
    if len(events) == 0:
        print("[Debug] Warning: No events found. Injecting dummy events for testing.")
        # Inject some events if empty
        event_bus.publish(Event("user_input", "user", {"content": "我喜欢吃苹果"}))
        event_bus.publish(Event("driver_response", "driver", {"content": "好的，记住了。"}))
        events = event_bus.get_latest_cycle(limit=2)
    
    # 3. Manually Trigger generate_diary
    # This bypasses the threading lock check in request_diary_generation
    # and calls the logic directly to see output in this terminal
    print("\n[Debug] Triggering generate_diary() directly...")
    
    try:
        # We might need to mock the time.sleep(5) to save time, but let's keep it 
        # to match real behavior, or monkeypatch it.
        # Let's monkeypatch sleep for speed
        original_sleep = time.sleep
        time.sleep = lambda x: print(f"[Debug] Skipped sleep({x})")
        
        nav.generate_diary()
        
        # Restore sleep
        time.sleep = original_sleep
        
        print("\n[Debug] generate_diary() returned.")
        
    except Exception as e:
        print(f"\n[Debug] Exception during generate_diary: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_navigator_cycle()
