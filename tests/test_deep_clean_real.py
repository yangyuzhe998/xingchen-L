import sys
import os
import json
import time
import sqlite3

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.navigator.engine import Navigator
from src.config.settings.settings import settings

def setup_dummy_data():
    """Populate storage.json with dummy data for testing"""
    print("[Test] Generating dummy memory data...")
    dummy_data = []
    for i in range(30):
        dummy_data.append({
            "content": f"User ate apple number {i} on day {i}.",
            "category": "fact",
            "created_at": "2023-01-01T12:00:00",
            "metadata": {"source": "test"}
        })
    
    # Ensure dir exists
    os.makedirs(os.path.dirname(settings.MEMORY_STORAGE_PATH), exist_ok=True)
    
    with open(settings.MEMORY_STORAGE_PATH, 'w', encoding='utf-8') as f:
        json.dump(dummy_data, f, ensure_ascii=False, indent=2)
    print(f"[Test] Created {len(dummy_data)} items in storage.json")

def verify_archive():
    """Verify archive.db content"""
    print("\n[Test] Verifying archive.db...")
    if not os.path.exists(settings.ARCHIVE_DB_PATH):
        print("[Test] FAILURE: archive.db not found.")
        return

    conn = sqlite3.connect(settings.ARCHIVE_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM raw_memories")
    count = cursor.fetchone()[0]
    print(f"[Test] Archive DB count: {count}")
    
    cursor.execute("SELECT content FROM raw_memories LIMIT 3")
    rows = cursor.fetchall()
    print("[Test] Sample archived memories:")
    for row in rows:
        print(f"  - {row[0]}")
    conn.close()

def verify_storage():
    """Verify storage.json content (should be summarized)"""
    print("\n[Test] Verifying storage.json...")
    with open(settings.MEMORY_STORAGE_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"[Test] Storage JSON count: {len(data)}")
    print("[Test] Current storage content:")
    for item in data:
        print(f"  - {item.get('content')}")

def run_test():
    # 1. Setup
    setup_dummy_data()
    
    # 2. Init Navigator (S-Brain)
    print("\n[Test] Initializing Navigator (S-Brain)...")
    nav = Navigator(name="TestNavigator")
    
    # 3. Trigger Deep Clean
    print("\n[Test] Triggering Deep Clean manually...")
    # We call the method directly on the manager instance
    nav.deep_clean_manager.perform_deep_clean(trigger="manual_test")
    
    # 4. Verify
    verify_archive()
    verify_storage()

if __name__ == "__main__":
    run_test()
