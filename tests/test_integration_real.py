
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
from src.core.bus.event_bus import event_bus

def test_real_integration():
    print("=== 开始真实环境集成测试: F-Brain & S-Brain ===")
    
    # Check API Keys
    if not os.getenv("DASHSCOPE_API_KEY") and not os.getenv("QWEN_API_KEY"):
        print("⚠️ Warning: Qwen API Key not found. Driver might fail.")
    if not os.getenv("DEEPSEEK_API_KEY"):
        print("⚠️ Warning: DeepSeek API Key not found. Navigator might fail.")

    # 1. 初始化核心组件
    print("\n[1/5] 初始化组件...")
    memory = Memory()
    
    # 初始化 LibraryManager & ShellManager
    library_manager.set_memory(memory)
    library_manager.scan_and_index()
    shell_manager.set_memory(memory)
    shell_manager.scan_and_index()
    
    # 初始化 Driver (F脑)
    driver = Driver(memory=memory)
    
    # 注册 run_shell_command 工具 (如果未注册)
    from src.tools.registry import tool_registry, ToolTier
    
    if not tool_registry.get_tool("run_shell_command"):
        @tool_registry.register(
            name="run_shell_command",
            description="执行 Shell 命令。请谨慎使用，仅执行只读或安全的命令。",
            tier=ToolTier.FAST,
            schema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "要执行的 Shell 命令 (e.g., 'ls -la', 'git log')"
                    }
                },
                "required": ["command"]
            }
        )
        def run_shell_command(command):
            # 简单的 Mock 实现，或者调用 subprocess
            # 为了安全起见，在测试脚本里我们只打印，不真执行
            print(f"[TEST ENV] 💻 Executing Shell Command: {command}")
            # 模拟 git log 输出
            if "git log" in command:
                return "a1b2c3d Fix bug in login\ne5f6g7h Update README\ni9j0k1l Initial commit"
            return f"Command '{command}' executed successfully."

    # 初始化 Navigator (S脑)
    navigator = Navigator(memory=memory)
    memory.set_navigator(navigator) # Link back
    
    # 2. 准备测试数据
    print("\n[2/5] 准备上下文 (Case Injection)...")
    # 确保有一个相关的案例，方便 Driver 检索
    shell_manager.add_command_case(
        command="git log --oneline -n 3",
        scenario="查看最近的3条简略提交记录",
        outcome="成功显示",
        trust_score=0.98
    )

    # 3. 测试 Driver (F脑) - 真实 LLM 调用
    print("\n[3/5] 测试 F-Brain (Driver) 真实思考...")
    user_input = "我想看看最近的3次提交，简略一点就行，帮我查查。"
    print(f"User: {user_input}")
    
    try:
        # 真实调用
        start_time = time.time()
        response = driver.think(user_input)
        duration = time.time() - start_time
        
        print(f"Agent ({duration:.2f}s): {response}")
        
    except Exception as e:
        print(f"❌ Driver 运行出错: {e}")
        return

    # 4. 模拟 EventBus 数据积累
    # Driver.think 已经自动发布了 user_input 和 driver_response 事件
    # 我们再手动发几个心跳，凑够一轮分析
    print("\n[4/5] 准备 S-Brain 分析数据...")
    
    # 5. 测试 Navigator (S脑) - 真实 LLM 调用
    print("\n[5/5] 测试 S-Brain (Navigator) 真实深度推理...")
    try:
        # 强制触发分析
        start_time = time.time()
        suggestion, delta = navigator.analyze_cycle()
        duration = time.time() - start_time
        
        print(f"S-Brain Analysis ({duration:.2f}s):")
        print(f"-> Suggestion: {suggestion}")
        print(f"-> Delta: {delta}")
        
        # 打印生成的 Suggestion Board
        if navigator.suggestion_board:
            print(f"-> Board: {navigator.suggestion_board}")
            
    except Exception as e:
        print(f"❌ Navigator 运行出错: {e}")

    print("\n=== 测试结束 ===")

if __name__ == "__main__":
    test_real_integration()
