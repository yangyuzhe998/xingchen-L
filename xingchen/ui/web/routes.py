import os
from fastapi import APIRouter, Request, HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from xingchen.config.settings import settings
from xingchen.utils.logger import logger
from xingchen.core.event_bus import event_bus
from xingchen.schemas.events import EventType, BaseEvent as Event
from sse_starlette.sse import EventSourceResponse
from .sse import sse_manager

router = APIRouter()

# 获取模板目录
templates_path = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_path)

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

def verify_api_key(api_key: str = Security(api_key_header)):
    """验证 API Key"""
    if not api_key:
        return None
    # 支持 Bearer 格式
    token = api_key.replace("Bearer ", "")
    if token != settings.WEB_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return token

class ChatRequest(BaseModel):
    content: str

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """首页"""
    return templates.TemplateResponse(request, "index.html")

@router.post("/api/chat")
async def chat(req: ChatRequest, token: str = Depends(verify_api_key)):
    """发送聊天消息"""
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
        
    logger.info(f"[WebAPI] Received chat: {req.content}")
    
    # 发布用户输入事件
    event_bus.publish(Event(
        type=EventType.USER_INPUT,
        source="web_ui",
        payload={"content": req.content},
        meta={}
    ))
    
    return {"status": "ok"}

@router.get("/api/stream")
async def stream(request: Request, key: str = None):
    """SSE 事件流"""
    # 允许通过 query param 验证 key (方便 EventSource 调用)
    if key != settings.WEB_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid key")
        
    return EventSourceResponse(sse_manager.event_generator())

@router.get("/api/status")
async def status(key: str = None):
    """获取系统状态"""
    if key != settings.WEB_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid key")
        
    # 这里可以返回更详细的运行统计
    return {
        "status": "running",
        "uptime": "TODO",
        "memory_stats": "TODO"
    }
