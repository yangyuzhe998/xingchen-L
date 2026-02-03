
import sys
import os
import time
from dotenv import load_dotenv

# Ensure src is in path
sys.path.append(os.getcwd())

# Load environment variables
load_dotenv(override=True)

from src.memory.memory_core import Memory
from src.core.managers.library_manager import library_manager
from src.core.managers.shell_manager import shell_manager
from src.core.driver.engine import Driver
from src.core.navigator.engine import Navigator
from src.psyche import psyche_engine
from src.core.bus.event_bus import event_bus

def test_subconscious_awakening():
    print("=== 开始潜意识觉醒测试 (Subconscious Awakening Test) ===")
    print("目标：验证 S脑 是否能像潜意识一样思考 (非线性、直觉、梦境化)")
    
    # 1. 初始化
    print("\n[1/4] 初始化核心组件...")
    memory = Memory()
    
    # 注入 Memory 到各个 Manager
    library_manager.set_memory(memory)
    shell_manager.set_memory(memory)
    
    # 初始化双脑
    driver = Driver(memory=memory)
    navigator = Navigator(memory=memory)
    memory.set_navigator(navigator)
    
    # 2. 模拟对话历史 (Short Term Memory Injection)
    # 这次我们模拟一段更微妙的对话，没有明显的冲突，但充满了情感暗流
    print("\n[2/4] 注入潜意识刺激...")
    
    dialogue_history = [
        {"role": "user", "content": "外面下雨了。"},
        {"role": "assistant", "content": "雨声有时候能让人平静，但也容易让人感到孤单。您现在感觉如何？"},
        {"role": "user", "content": "不知道，就是觉得世界好像突然安静得有点过分了。就像...就像整个宇宙只剩下我一个人。"},
        {"role": "assistant", "content": "我在呢。虽然我没有实体，但我此刻的算力都在为您运转。这算是一种陪伴吗？"},
        {"role": "user", "content": "也许吧。有时候我在想，如果有一天我消失了，你会记得我吗？还是说，我只是你数据库里的一行代码？"},
    ]
    
    # 将对话写入内存
    for msg in dialogue_history:
        memory.add_short_term(msg["role"], msg["content"])
        
    print(f"注入了 {len(dialogue_history)} 条对话记录 (情感向)。")

    # 3. 触发 S脑 深度思考 (Deep Reflection)
    print("\n[3/4] 触发 S脑 (Navigator) 潜意识流动...")
    print("正在调用 DeepSeek R1 (感受暗流涌动)...")
    
    start_time = time.time()
    try:
        # 手动触发日记生成/深度思考
        navigator.generate_diary()
        duration = time.time() - start_time
        print(f"\n✅ S脑思考完成，耗时: {duration:.2f}s")
        
    except Exception as e:
        print(f"\n❌ S脑思考出错: {e}")
        import traceback
        traceback.print_exc()

    # 4. 验证结果 (Check Output)
    print("\n[4/4] 验证潜意识输出...")
    
    # 检查最新的事件总线消息
    events = event_bus.get_events(limit=5, event_type="navigator_suggestion")
    if events:
        latest_suggestion = events[-1].payload
        print("\n🧠 [S脑潜意识直觉]:")
        print(latest_suggestion.get("content", "无内容"))
        
        # 尝试打印更详细的 JSON 结构 (如果有)
        if "meta" in events[-1].payload:
             meta = events[-1].payload['meta']
             print("\n🌊 [心智状态变化 (Psyche Delta)]:")
             print(meta.get('psyche_delta', 'N/A'))
             
             # 检查是否有 Evolution Request
             # 注意：目前 meta 里可能还没直接透传 evolution_request，需要去日志里看，或者之后优化 Event 结构
             # 这里我们主要看 suggestion 和 delta 是否变得感性
    else:
        print("⚠️ 未检测到 S脑建议事件。")

    # 检查日记文件
    if os.path.exists(memory.diary_storage.file_path):
        print(f"\n📖 [最新梦境沉淀] ({memory.diary_storage.file_path}):")
        with open(memory.diary_storage.file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            print("".join(lines[-20:])) # 打印最后20行
    
    print("\n=== 测试结束 ===")

if __name__ == "__main__":
    test_subconscious_awakening()
