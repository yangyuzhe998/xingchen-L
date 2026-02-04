import os
import sys
import json
import time

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.driver.engine import Driver
from src.memory.memory_core import Memory
from src.memory.storage.graph import GraphMemory

def verify_driver_memory_retrieval():
    print("=== Verifying Driver Memory Retrieval Fix ===")
    
    # 1. Setup Mock Memory
    test_graph_path = "tests/test_data/verify_graph.json"
    if os.path.exists(test_graph_path):
        os.remove(test_graph_path)
        
    memory = Memory(graph_path=test_graph_path)
    
    # 2. Inject User Profile into Graph
    print("Injecting 'User Profile' into Graph...")
    memory.graph_storage.add_triplet("用户", "is_named", "杨先生", relation_type="attribute")
    memory.graph_storage.add_triplet("用户", "role", "father_figure", relation_type="social", meta={"emotion_tag": "loving"})
    
    # 3. Initialize Driver
    driver = Driver(memory=memory)
    
    # 4. Simulate 'think' call
    user_input = "我是谁"
    print(f"\nUser Input: {user_input}")
    
    # We intercept the LLM call or just check the prompt construction by inspecting the logs/print output
    # Since we can't easily mock the LLM here without a mock library, we will rely on the printed 'long_term_context' 
    # inside the driver.think method (we added print statements previously or we can infer from behavior).
    # However, to be sure, let's just run it. If LLM is connected, it will use the context.
    
    try:
        response = driver.think(user_input)
        print(f"\nDriver Response: {response}")
        
        # 5. Check if response contains "杨先生"
        if "杨先生" in response:
            print("\n[SUCCESS] Driver correctly identified the user!")
        else:
            print("\n[FAILURE] Driver failed to identify the user.")
            
    except Exception as e:
        print(f"Error during verification: {e}")

if __name__ == "__main__":
    verify_driver_memory_retrieval()
