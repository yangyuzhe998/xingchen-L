import json
import asyncio
from typing import AsyncGenerator
from sse_starlette.sse import EventSourceResponse
from xingchen.core.event_bus import event_bus
from xingchen.utils.logger import logger

class SSEManager:
    """
    SSE 事件管理器
    负责监听 EventBus 并推送到 Web 端
    """
    def __init__(self):
        self.queue = asyncio.Queue()
        event_bus.subscribe(self._on_bus_event)

    def _on_bus_event(self, event):
        """将 EventBus 事件同步到异步队列"""
        try:
            # 过滤需要推送到前端的事件
            if event.type in ["driver_response", "psyche_update", "system_heartbeat", "system_notification"]:
                # 在异步循环中放入队列
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.call_soon_threadsafe(self.queue.put_nowait, event)
        except Exception as e:
            pass

    async def event_generator(self) -> AsyncGenerator[dict, None]:
        """SSE 生成器"""
        while True:
            try:
                event = await self.queue.get()
                
                # 转换格式适配前端
                if event.type == "driver_response":
                    yield {
                        "data": json.dumps({
                            "role": "assistant",
                            "content": event.get_content(),
                            "meta": event.meta
                        }, ensure_ascii=False)
                    }
                elif event.type == "psyche_update":
                    yield {
                        "data": json.dumps({
                            "role": "system_status",
                            "content": "psyche_update",
                            "meta": event.meta
                        }, ensure_ascii=False)
                    }
                elif event.type == "system_heartbeat":
                    yield {
                        "data": json.dumps({
                            "role": "system_status",
                            "content": "heartbeat",
                            "meta": event.meta
                        }, ensure_ascii=False)
                    }
                elif event.type == "system_notification":
                    yield {
                        "data": json.dumps({
                            "role": "system",
                            "content": event.get_content(),
                            "meta": event.meta
                        }, ensure_ascii=False)
                    }
            except Exception as e:
                logger.error(f"[SSE] Generator error: {e}")
                await asyncio.sleep(1)

sse_manager = SSEManager()
