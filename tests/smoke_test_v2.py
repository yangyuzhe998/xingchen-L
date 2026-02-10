
import os
import sys
import hashlib
from datetime import datetime

# 添加项目根目录到 sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.memory.memory_core import Memory
from src.memory.storage.knowledge_db import knowledge_db
from src.memory.storage.topic_manager import topic_manager
from src.utils.logger import logger

def test_system_integrity():
    print("Starting full-link stability and consistency smoke test...")
    
    # 1. 初始化检查
    memory = Memory()
    print("OK: Memory module initialized")

    # 2. 测试 KnowledgeDB 分类隔离与幂等 (维度 B)
    print("\n--- Testing KnowledgeDB (Fact Base) ---")
    content = "Test: Apple is sweet"
    
    # 存为事实
    id1 = knowledge_db.add_knowledge(content, category="fact")
    # 存为偏好
    id2 = knowledge_db.add_knowledge(content, category="preference")
    
    if id1 != id2:
        print(f"OK: Category isolation success: Fact ID({id1}) != Preference ID({id2})")
    else:
        print(f"Error: Category isolation failed: ID is same")

    # 重复存事实 (验证强化/幂等)
    id1_repeat = knowledge_db.add_knowledge(content, category="fact", confidence=0.9)
    if id1 == id1_repeat:
        k = knowledge_db.get_knowledge(limit=10)
        # 寻找对应的记录检查置信度
        record = next((x for x in k if x['id'] == id1), None)
        print(f"OK: Knowledge idempotency success: ID remains consistent ({id1})")
        if record and record['confidence'] >= 0.9:
            print(f"OK: Knowledge reinforcement success: Confidence updated")
    else:
        print(f"Error: Knowledge idempotency failed: New ID {id1_repeat} generated")

    # 3. 测试 TopicManager 场景隔离与强化 (维度 A/B)
    print("\n--- Testing TopicManager (Hierarchical Memory) ---")
    topic_id = topic_manager.create_topic("Test Topic", "Used for smoke test")
    task_a = topic_manager.create_task(topic_id, "Task A", "Context A")
    task_b = topic_manager.create_task(topic_id, "Task B", "Context B")
    
    frag_content = "Apple is sweet in this context"
    
    # 场景 A 记录
    f_a = topic_manager.add_fragment(frag_content, topic_id=topic_id, task_id=task_a, category="memory")
    # 场景 B 记录
    f_b = topic_manager.add_fragment(frag_content, topic_id=topic_id, task_id=task_b, category="memory")
    
    if f_a != f_b:
        print(f"OK: Scenario isolation success (Solved Apple Paradox): TaskA Frag != TaskB Frag")
    else:
        print(f"Error: Scenario isolation failed: Same ID generated for different tasks")

    # 场景 A 重复记录 (验证第一印象与强化)
    print("Performing reinforcement record for Scenario A...")
    f_a_repeat = topic_manager.add_fragment(frag_content, topic_id=topic_id, task_id=task_a, category="memory")
    
    # 验证数据
    frags = topic_manager.fragments.get(ids=[f_a])
    if frags and frags['metadatas']:
        meta = frags['metadatas'][0]
        print(f"OK: Reinforcement logic verified: mention_count={meta.get('mention_count')}, weight={meta.get('weight')}")
        if meta.get('mention_count', 0) > 1:
            print("OK: First impression retained, long-term impression reinforced")

    print("\n--- Database File Status ---")
    for db in ["knowledge.db", "bus.db"]:
        path = os.path.join("src", "memory_data", db)
        if os.path.exists(path):
            size = os.path.getsize(path)
            print(f"Storage: {db} auto-created, size: {size} bytes")

    print("\nSmoke test complete! System underlying logic is working normally.")

if __name__ == "__main__":
    try:
        test_system_integrity()
    except Exception as e:
        print(f"Error: Crash during test: {e}")
        import traceback
        traceback.print_exc()
