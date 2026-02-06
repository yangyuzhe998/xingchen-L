from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, Union
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

# 具体事件的 Payload 定义
class UserInputPayload(BaseModel):
    content: str

class DriverResponsePayload(BaseModel):
    content: str

class ProactiveInstructionPayload(BaseModel):
    content: Union[str, Dict[str, Any]] # 支持字符串或字典结构

class SystemHeartbeatPayload(BaseModel):
    content: str

class MemoryFullPayload(BaseModel):
    """Memory Full 事件负载"""
    type: str = "memory_full"
    count: int

class NavigatorSuggestionPayload(BaseModel):
    """Navigator 建议负载"""
    content: str

class CycleEndPayload(BaseModel):
    """Cycle End 事件负载 (暂留空，未来扩展)"""
    pass

class BaseEvent(BaseModel):
    """基础事件模型"""
    id: Optional[int] = None
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = Field(default_factory=time.time)
    type: EventType
    source: str
    # 强化 Payload 类型，允许特定的 Payload 模型或通用 Dict
    payload: Union[
        UserInputPayload, 
        DriverResponsePayload, 
        ProactiveInstructionPayload, 
        SystemHeartbeatPayload,
        MemoryFullPayload,
        NavigatorSuggestionPayload,
        CycleEndPayload,
        Dict[str, Any]
    ] = Field(default_factory=dict)
    meta: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True
        extra = "allow" # 允许额外的字段，保证兼容性

    @property
    def payload_data(self) -> Dict[str, Any]:
        """统一获取 Payload 的字典形式 (Helper)"""
        if hasattr(self.payload, 'model_dump'):
            return self.payload.model_dump()
        elif hasattr(self.payload, 'dict'):
            return self.payload.dict()
        elif isinstance(self.payload, dict):
            return self.payload
        else:
            return {}

    def get_content(self) -> Any:
        """快捷获取 content 字段 (安全访问)"""
        return self.payload_data.get('content', '')
