import sys
import os
import argparse
import uvicorn
import asyncio
import io

# 强制设置环境编码为 UTF-8 (解决 Windows 终端乱码)
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    os.environ["PYTHONUTF8"] = "1"

from src.utils.logger import logger

# 添加项目根目录到 sys.path
# 我们需要从 src/ 上跳一级到项目根目录
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def start_cli():
    """启动调试 CLI 模式"""
    from src.core.driver.engine import Driver
    from src.core.navigator.core import Navigator
    from src.psyche import psyche_engine
    from src.memory.memory_core import Memory
    from src.core.managers import CycleManager
    from src.ui.debug_app import DebugCLI
    from src.tools.loader import load_all_tools

    logger.info("正在初始化 CLI 模式组件...")
    
    # 加载工具
    load_all_tools()
    
    memory = Memory()
    psyche = psyche_engine
    navigator = Navigator(memory=memory)
    # memory.set_navigator(navigator) # 已解耦
    driver = Driver(memory=memory)
    cycle_manager = CycleManager(navigator, psyche)
    
    app = DebugCLI()
    
    def handler(content):
        # 同步桥接到 Driver
        psyche_state = psyche.state
        driver.think(content, psyche_state=psyche_state)

    app.set_input_handler(handler)
    
    try:
        app.run()
    finally:
        cycle_manager.running = False
        logger.info("系统关闭。")

def create_app():
    """Uvicorn 工厂函数"""
    from src.core.driver.engine import Driver
    from src.core.navigator.core import Navigator
    from src.psyche import psyche_engine
    from src.memory.memory_core import Memory
    from src.core.managers import CycleManager
    from src.ui.web_app import web_ui
    from src.tools.loader import load_all_tools
    
    logger.info("正在初始化 Web 模式组件...")

    # 加载工具
    load_all_tools()
    
    # 初始化核心组件
    memory = Memory()
    psyche = psyche_engine
    navigator = Navigator(memory=memory)
    # memory.set_navigator(navigator) # 已通过 EventBus 解耦
    driver = Driver(memory=memory)
    cycle_manager = CycleManager(navigator, psyche)
    
    # 绑定 Web UI 处理器
    async def handler(content):
        psyche_state = psyche.state
        # 在线程池中运行以避免阻塞异步循环
        await asyncio.to_thread(driver.think, content, psyche_state=psyche_state)

    web_ui.set_input_handler(handler)
    
    return web_ui.app

# 为 Uvicorn 暴露 app 对象
if os.environ.get("LAUNCH_MODE") == "web":
    app = create_app()

def start_web():
    """启动 Web Server 模式 (同步入口)"""
    os.environ["LAUNCH_MODE"] = "web"
    # 重新导入以触发 app 创建
    import importlib
    import src.main
    importlib.reload(src.main)
    
    logger.info("正在启动 Uvicorn 服务器...")
    logger.info("\n🌐 Web UI 访问地址: http://127.0.0.1:8000\n")
    
    uvicorn.run("src.main:app", host="127.0.0.1", port=8000, log_level="info", reload=False)


def main():
    parser = argparse.ArgumentParser(description="星辰-V 启动器")
    parser.add_argument("mode", nargs="?", choices=["cli", "web"], default="cli", help="启动模式 (cli 或 web)")
    
    args = parser.parse_args()
    
    if args.mode == "web":
        start_web()
    else:
        start_cli()

if __name__ == "__main__":
    main()
