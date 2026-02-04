import sys
import os
import time

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.memory.memory_core import Memory
from src.core.driver.engine import Driver

def test_alias_resolution():
    print("=== Testing Fuzzy Alias Resolution ===")
    
    # 1. Initialize Memory
    memory = Memory()
    
    # 2. Simulate S-Brain learning an alias
    print("\n[Phase 1] Learning Alias...")
    aliases = [
        ("仔仔", "用户"),
        ("老杨", "用户"),
        ("XingChen", "AI"),
        ("奥巴马", "President"),
        ("特朗普", "President")
    ]
    
    for a, t in aliases:
        memory.save_alias(a, t)
    
    # Wait for vector db to index
    time.sleep(1)
    
    # 3. Simulate F-Brain retrieval
    print("\n[Phase 2] F-Brain Retrieval...")
    driver = Driver(name="TestDriver", memory=memory)
    
    # Test cases
    test_cases = [
        ("仔仔今天有点累", "用户"),
        ("老杨饿了", "用户"),
        ("川普是谁", "President"), # "川普" should be close to "特朗普"
        ("这里有个大帅哥", None),   # Should hopefully not match or have high distance
        ("天气怎么样", None)
    ]
    
    print(f"\n{'Query':<20} | {'Expected':<10} | {'Actual Alias':<10} | {'Target':<10} | {'Dist':<6}")
    print("-" * 70)
    
    for query, expected_target in test_cases:
        match = memory.search_alias(query, threshold=0.4) # Strict threshold
        
        actual_alias = match[0] if match else "None"
        actual_target = match[1] if match else "None"
        dist = f"{match[2]:.4f}" if match else "N/A"
        
        print(f"{query:<20} | {str(expected_target):<10} | {actual_alias:<10} | {actual_target:<10} | {dist:<6}")


if __name__ == "__main__":
    test_alias_resolution()
