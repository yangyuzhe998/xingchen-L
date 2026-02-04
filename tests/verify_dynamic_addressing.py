import os
import sys
import json

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.driver.engine import Driver
from src.memory.memory_core import Memory
from src.psyche.core.engine import PsycheEngine

def verify_dynamic_addressing():
    print("=== Verifying Dynamic Addressing & Intimacy ===")
    
    # 1. Initialize Components
    test_graph_path = "tests/test_data/verify_graph.json" # Reuse existing populated graph
    memory = Memory(graph_path=test_graph_path)
    psyche = PsycheEngine() # This loads/creates the default state file
    driver = Driver(memory=memory)

    # 2. Reset Intimacy to Low and Test
    print("\n--- Test 1: Low Intimacy (0.1) ---")
    psyche.state["dimensions"]["intimacy"]["value"] = 0.1
    psyche.update_state({}) # Trigger narrative update
    print(f"Psyche Narrative: {psyche.get_state_summary()}")
    
    response_low = driver.think("我是谁")
    print(f"Response (Low): {response_low}")
    
    # 3. Boost Intimacy to High and Test
    print("\n--- Test 2: High Intimacy (0.9) ---")
    psyche.state["dimensions"]["intimacy"]["value"] = 0.9
    psyche.update_state({}) # Trigger narrative update
    print(f"Psyche Narrative: {psyche.get_state_summary()}")
    
    response_high = driver.think("我是谁")
    print(f"Response (High): {response_high}")
    
    # 4. Verification
    if "先生" in response_low and ("先生" not in response_high or "您" not in response_high):
        print("\n[SUCCESS] Dynamic addressing working as expected!")
    else:
        print("\n[PARTIAL/FAILURE] Check responses manually.")

if __name__ == "__main__":
    verify_dynamic_addressing()
