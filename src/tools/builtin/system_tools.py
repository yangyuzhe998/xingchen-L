
from datetime import datetime
from ..registry import ToolRegistry
from ..definitions import ToolTier

@ToolRegistry.register(
    name="get_current_time",
    description="获取当前系统时间。无需参数。",
    tier=ToolTier.FAST,
    schema={
        "type": "object",
        "properties": {},
        "required": []
    }
)
def get_current_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@ToolRegistry.register(
    name="calculate",
    description="执行简单的数学计算 (Python eval)。",
    tier=ToolTier.FAST,
    schema={
        "type": "object",
        "properties": {
            "expression": {"type": "string", "description": "数学表达式，例如 '2 + 2'"}
        },
        "required": ["expression"]
    }
)
def calculate(expression: str):
    try:
        # 安全限制：仅允许简单算术
        allowed = set("0123456789+-*/(). ")
        if not all(c in allowed for c in expression):
            return "Error: 仅支持简单算术表达式 (0-9, +, -, *, /, (, ))"
        return str(eval(expression))
    except Exception as e:
        return f"Error: {e}"
