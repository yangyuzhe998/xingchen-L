
import sys
import os

# Add src to path
sys.path.append(os.getcwd())

from src.memory.memory_core import Memory
from src.core.library_manager import library_manager

def test_library():
    print("🚀 Initializing Memory & Library...")
    memory = Memory()
    library_manager.set_memory(memory)
    
    print("\n📦 Scanning and Indexing...")
    library_manager.scan_and_index()
    
    print("\n🔍 Testing Search: 'What is the weather in Beijing?'")
    results = library_manager.search_skills("What is the weather in Beijing?")
    
    print(f"Found {len(results)} results:")
    for r in results:
        print(f" - [{r['name']}] {r['description']} (ID: {r['id']})")
        
    if results:
        print("\n📖 Checking out first result...")
        content = library_manager.checkout_skill(r['path'])
        print(f"--- Content Start ---\n{content[:100]}...\n--- Content End ---")

if __name__ == "__main__":
    test_library()
