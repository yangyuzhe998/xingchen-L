
import sys
import os
import time
import threading
import random
import logging

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.bus.event_bus import event_bus, Event
from src.memory.memory_core import Memory
from src.utils.logger import logger
from src.config.settings.settings import settings

# Configure test parameters
NUM_THREADS = 10
EVENTS_PER_THREAD = 50
MEMORY_WRITES_PER_THREAD = 20

def simulate_user_activity(thread_id, memory):
    """Simulate a user interacting with the system"""
    logger.info(f"[TestThread-{thread_id}] Started.")
    
    for i in range(EVENTS_PER_THREAD):
        # Publish Event
        content = f"Stress Test Message {i} from Thread {thread_id}"
        event_bus.publish(Event(
            type="user_input",
            source=f"user_thread_{thread_id}",
            payload={"content": content},
            meta={"thread": thread_id, "seq": i}
        ))
        
        # Simulate Memory Write (Short Term)
        if i < MEMORY_WRITES_PER_THREAD:
            memory.add_short_term(role="user", content=content)
            
        # Random sleep to simulate real-world jitter (0-10ms)
        time.sleep(random.random() * 0.01)

    logger.info(f"[TestThread-{thread_id}] Finished.")

def stress_test():
    print("Starting Stress Test...")
    print(f"Threads: {NUM_THREADS}")
    print(f"Events per Thread: {EVENTS_PER_THREAD}")
    print(f"Memory Writes per Thread: {MEMORY_WRITES_PER_THREAD}")
    print(f"Log File: {settings.LOG_FILE}")
    
    # Initialize Memory
    memory = Memory()
    
    start_time = time.time()
    
    threads = []
    for i in range(NUM_THREADS):
        t = threading.Thread(target=simulate_user_activity, args=(i, memory))
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
        
    end_time = time.time()
    duration = end_time - start_time
    
    total_events = NUM_THREADS * EVENTS_PER_THREAD
    print(f"\nStress Test Completed in {duration:.2f} seconds.")
    print(f"Throughput: {total_events / duration:.2f} events/sec")
    
    # Verify Logs
    print("\nVerifying Log File...")
    if os.path.exists(settings.LOG_FILE):
        with open(settings.LOG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            print(f"Log File contains {len(lines)} lines.")
            # Simple check for the last log entry
            print(f"Last Log Entry: {lines[-1].strip()}")
    else:
        print("❌ Log file not found!")

if __name__ == "__main__":
    stress_test()
