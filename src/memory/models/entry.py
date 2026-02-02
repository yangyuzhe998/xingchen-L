from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any

@dataclass
class ShortTermMemoryEntry:
    """短期对话记忆条目"""
    role: str # user | assistant | system
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp
        }

@dataclass
class LongTermMemoryEntry:
    """长期事实记忆条目"""
    content: str
    category: str = "fact" # fact | rule | preference
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "category": self.category,
            "created_at": self.created_at,
            "metadata": self.metadata
        }
