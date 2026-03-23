import sys
import os
import argparse
import uvicorn
from xingchen.app import app_context
from xingchen.utils.logger import logger


def start_cli():
    """启动调试 CLI 模式"""
    from xingchen.ui.cli import DebugCLI
    
    # 初始化核心组件
    app_context.initialize()
    
    # 初始化 CLI 界面
    cli = DebugCLI()
    
    # 注入同步思考处理器
    cli.set_input_handler(app_context.get_driver_handler())
    
    try:
        cli.run()
    finally:
        app_context.shutdown()


def start_web():
    """启动 Web Server 模式"""
    from xingchen.ui.web.app import create_web_app
    from xingchen.core.event_bus import event_bus
    from xingchen.schemas.events import EventType
    import asyncio

    # 初始化核心组件
    app_context.initialize()
    
    # 创建 FastAPI 应用
    web_app = create_web_app()
    
    # 共享事件循环引用
    loop_container = {"loop": None}

    @web_app.on_event("startup")
    async def capture_loop():
        loop_container["loop"] = asyncio.get_running_loop()
        logger.info("[Main] Captured running event loop for EventBus bridge.")

    # 获取异步思考处理器
    async_handler = app_context.get_async_driver_handler()
    
    # 监听 EventBus 上的用户输入事件并桥接到 Driver
    def on_user_input(event):
        if event.type == EventType.USER_INPUT:
            content = event.get_content()
            if not content:
                return
                
            # 将同步的 EventBus 回调转给异步循环执行耗时任务
            try:
                loop = loop_container["loop"]
                if loop and loop.is_running():
                    asyncio.run_coroutine_threadsafe(async_handler(content), loop)
                else:
                    logger.warning("[Main] Event loop not yet captured or not running.")
            except Exception as e:
                logger.error(f"[Main] Failed to dispatch user input: {e}")

    event_bus.subscribe(on_user_input)
    
    logger.info("正在启动 Uvicorn 服务器...")
    logger.info(f"\n🌐 Web UI 访问地址: http://127.0.0.1:8000?key=YOUR_API_KEY\n")
    
    # 启动服务器
    uvicorn.run(web_app, host="127.0.0.1", port=8000, log_level="info")


def main():
    """启动器主入口"""
    parser = argparse.ArgumentParser(description="星辰-V (XingChen-V) 启动器")
    parser.add_argument("mode", nargs="?", choices=["cli", "web"], default="cli", help="启动模式 (cli 或 web)")
    
    args = parser.parse_args()
    
    # 确保当前目录在 sys.path 中
    sys.path.append(os.getcwd())
    
    if args.mode == "web":
        start_web()
    else:
        start_cli()


if __name__ == "__main__":
    main()
