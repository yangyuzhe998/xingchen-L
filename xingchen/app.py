import asyncio
from xingchen.core.driver import Driver
from xingchen.core.navigator import Navigator
from xingchen.psyche import psyche_engine
from xingchen.memory.facade import Memory
from xingchen.core.cycle import CycleManager
from xingchen.tools.loader import load_all_tools
from xingchen.utils.logger import logger


class XingChenApp:
    """
    Application Factory (应用工厂)
    统一管理核心组件的生命周期与依赖注入。
    """
    def __init__(self):
        self.memory = None
        self.psyche = None
        self.navigator = None
        self.driver = None
        self.cycle_manager = None
        self._initialized = False

    def initialize(self):
        """初始化所有核心组件"""
        if self._initialized:
            return
            
        logger.info("[App] 🚀 正在初始化星辰-V 核心系统...")
        
        # 1. 加载内置工具 (注册到 ToolRegistry)
        load_all_tools()
        
        # 2. 初始化记忆系统 (含 WAL 恢复)
        self.memory = Memory()
        
        # 3. 初始化心智系统
        self.psyche = psyche_engine
        
        # 4. 初始化导航脑 (S脑) 与 驱动脑 (F脑)
        self.navigator = Navigator(memory=self.memory)
        self.driver = Driver(memory=self.memory)
        
        # 5. 启动周期管理器 (心跳、触发器、自动演化)
        self.cycle_manager = CycleManager(self.navigator, self.psyche)
        
        self._initialized = True
        logger.info("[App] ✅ 核心系统初始化完成。")

    def get_driver_handler(self):
        """获取同步 Driver 处理器 (用于 CLI)"""
        if not self._initialized:
            self.initialize()
            
        def handler(content):
            return self.driver.think(content, psyche_state=self.psyche.get_raw_state())
        return handler

    def get_async_driver_handler(self):
        """获取异步 Driver 处理器 (用于 Web)"""
        if not self._initialized:
            self.initialize()
            
        async def handler(content):
            # 在线程池中执行耗时的 LLM 思考过程，不阻塞 FastAPI 异步循环
            return await asyncio.to_thread(
                self.driver.think, 
                content, 
                psyche_state=self.psyche.get_raw_state()
            )
        return handler

    def shutdown(self):
        """优雅关闭"""
        if self.cycle_manager:
            self.cycle_manager.stop()
        if self.memory:
            self.memory.commit_long_term()
            self.memory.save_cache()
        logger.info("[App] 系统已优雅关闭。")


# 单例应用实例
app_context = XingChenApp()
