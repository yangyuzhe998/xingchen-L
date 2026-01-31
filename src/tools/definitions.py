
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, Any, Optional

class ToolTier(Enum):
    FAST = "fast" # F-Brain (Driver) 工具：零成本，本地执行，极速
    SLOW = "slow" # S-Brain (Navigator) 工具：高成本，复杂逻辑，可能联网

@dataclass
class ToolDefinition:
    name: str
    description: str
    func: Callable
    tier: ToolTier
    schema: Dict[str, Any] # JSON Schema for arguments
    enabled: bool = True
