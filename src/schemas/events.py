from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from enum import Enum
import uuid
import time

class EventType(str, Enum):
    USER_INPUT = "user_input"
    DRIVER_RESPONSE = "driver_response"
    NAVIGATOR_SUGGESTION = "navigator_suggestion"
    PROACTIVE_INSTRUCTION = "proactive_instruction"
    SYSTEM_HEARTBEAT = "system_heartbeat"
    SYSTEM_NOTIFICATION = "system_notification"
    MEMORY_WRITE = "memory_write"
    PSYCHE_UPDATE = "psyche_update"

class BaseEvent(BaseModel):
    """基础事件模型"""
    id: Optional[int] = None
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = Field(default_factory=time.time)
    type: EventType
    source: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    meta: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True
        extra = "allow" # 允许额外的字段，保证兼容性

# 具体事件的 Payload 定义 (可选，用于更严格的校验)
class UserInputPayload(BaseModel):
    content: str

class DriverResponsePayload(BaseModel):
    content: str

class ProactiveInstructionPayload(BaseModel):
    content: str | Dict[str, Any] # 支持字符串或字典结构
