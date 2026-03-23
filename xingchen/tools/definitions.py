from dataclasses import dataclass
from enum import Enum
from typing import Callable, Dict, Any

class ToolTier(Enum):
    FAST = "fast" # F-Brain (Driver) 工具
    SLOW = "slow" # S-Brain (Navigator) 工具

@dataclass
class ToolDefinition:
    name: str
    description: str
    func: Callable
    tier: ToolTier
    schema: Dict[str, Any]
    enabled: bool = True
