from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any

class ShortTermMemoryEntry(BaseModel):
    """短期对话记忆条目"""
    role: str # user | assistant | system
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

class LongTermMemoryEntry(BaseModel):
    """长期事实记忆条目"""
    content: str
    category: str = "fact" # fact | rule | preference
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        # 注意: Pydantic v2 使用 model_dump()
        return self.model_dump()
