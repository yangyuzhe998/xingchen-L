
import os
import asyncio
from typing import Dict, Any, Callable
from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel

from src.interfaces.ui_interface import UserInterface
from src.utils.logger import logger
from src.core.bus.event_bus import event_bus, Event

class WebApp(UserInterface):
    """
    基于 FastAPI 的 Web 用户界面
    实现 UserInterface 接口，作为后端的 UI 层
    """
    def __init__(self):
        self.app = FastAPI(title="XingChen-V Web UI")
        self.input_handler = None
        self._message_queue = asyncio.Queue()
        
        # Setup directories
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.template_dir = os.path.join(current_dir, "templates")
        self.static_dir = os.path.join(current_dir, "static")
        
        if not os.path.exists(self.template_dir):
            os.makedirs(self.template_dir)
        if not os.path.exists(self.static_dir):
            os.makedirs(self.static_dir)

        self.templates = Jinja2Templates(directory=self.template_dir)
        self.app.mount("/static", StaticFiles(directory=self.static_dir), name="static")
        
        self._main_loop = None

        # Register Routes
        self._register_routes()
        
        @self.app.on_event("startup")
        async def startup_event():
            self._main_loop = asyncio.get_running_loop()
            logger.info(f"Web UI Main Loop Captured: {self._main_loop}")
        
        # Subscribe to EventBus
        event_bus.subscribe(self._on_bus_event)

    def _register_routes(self):
        @self.app.get("/", response_class=HTMLResponse)
        async def read_root(request: Request):
            return self.templates.TemplateResponse("index.html", {"request": request})

        @self.app.post("/api/chat")
        async def chat(request: Request):
            data = await request.json()
            user_input = data.get("content")
            if not user_input:
                return {"status": "empty"}
            
            # Display user message (echo)
            # self.display_message("user", user_input) # Frontend does this optimistically
            
            # Trigger input handler
            if(self.input_handler):
                # Run in background to avoid blocking response
                asyncio.create_task(self._process_input(user_input))
                
            return {"status": "ok"}

        @self.app.get("/api/stream")
        async def stream(request: Request):
            """SSE Stream for pushing messages to frontend"""
            async def event_generator():
                while True:
                    if await request.is_disconnected():
                        break
                    
                    # Wait for new message
                    message = await self._message_queue.get()
                    yield {
                        "event": "message",
                        "data": message
                    }
            return EventSourceResponse(event_generator())

    async def _process_input(self, content):
        if self.input_handler:
            # Check if handler is async
            if asyncio.iscoroutinefunction(self.input_handler):
                await self.input_handler(content)
            else:
                # Run sync handler in thread pool
                await asyncio.to_thread(self.input_handler, content)

    def _on_bus_event(self, event: Event):
        """Handle EventBus events and push to frontend"""
        from src.schemas.events import EventType # Import enum
        
        # 使用 Enum 进行判断，或者兼容字符串
        # 注意: Pydantic 的 Event.type 是 EventType 枚举，但在 sqlite 里可能被存为字符串
        # EventBus 读取出来的是 Pydantic 对象，所以 type 是枚举成员
        
        event_type = event.type
        # 如果 event.type 是枚举，获取其 value
        if hasattr(event_type, "value"):
            event_type = event_type.value
            
        if event_type == EventType.DRIVER_RESPONSE.value:
            content = event.payload.get("content", "")
            meta = event.meta
            self.display_message("assistant", content, meta)
        
        elif event_type == EventType.NAVIGATOR_SUGGESTION.value:
            suggestion = event.payload.get("content", "")
            # Optional: push system notification
            pass

    # --- UserInterface Implementation ---

    def display_message(self, role: str, content: str, meta: Dict[str, Any] = None):
        """Push message to frontend via SSE"""
        import json
        msg_data = {
            "role": role,
            "content": content,
            "meta": meta or {}
        }
        
        # 1. 获取主循环 (WebApp 创建时所在的循环)
        # 注意：这里假设 WebApp 是在主线程初始化的
        try:
            # 尝试获取当前线程的 loop
            loop = asyncio.get_running_loop()
            # 如果成功，说明我们在主线程 (API 路由中)，直接放
            loop.create_task(self._message_queue.put(json.dumps(msg_data)))
        except RuntimeError:
            # 如果没有 running loop，说明我们在其他线程 (EventBus 线程)
            # 我们需要找到 Uvicorn 的主循环。这有点棘手，因为我们没有全局引用。
            # Hack: 使用 asyncio.run_coroutine_threadsafe 提交给我们在 __init__ 时捕获的 loop？
            # 或者更简单的：EventBus 回调是在线程池里，我们只要能找到主循环即可。
            # 实际上，FastAPI/Uvicorn 启动后，我们可以假设主循环是可访问的。
            
            # [Fix] 我们需要在 __init__ 里捕获 loop 吗？不，__init__ 时 uvicorn 还没启动 loop。
            # 我们使用一个全局变量或者在 startup 事件中捕获 loop。
            if hasattr(self, '_main_loop') and self._main_loop:
                 asyncio.run_coroutine_threadsafe(
                     self._message_queue.put(json.dumps(msg_data)), 
                     self._main_loop
                 )
            else:
                logger.warning("Main loop not captured, message dropped.")

    def set_input_handler(self, handler: Callable[[str], None]):
        self.input_handler = handler

    def update_status(self, status: str, details: Dict[str, Any] = None):
        pass

    def run(self):
        # WebApp is run by Uvicorn externally
        pass

# Global Instance
web_ui = WebApp()
app = web_ui.app
