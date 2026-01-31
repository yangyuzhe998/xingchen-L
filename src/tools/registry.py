
from typing import Dict, List, Any, Callable
from .definitions import ToolDefinition, ToolTier
import inspect
import json

class ToolRegistry:
    """
    工具注册中心 (Singleton)
    管理所有的 Agent 工具，支持按 Tier (Fast/Slow) 过滤。
    """
    _instance = None
    _tools: Dict[str, ToolDefinition] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ToolRegistry, cls).__new__(cls)
        return cls._instance

    @classmethod
    def register(cls, name: str, description: str, tier: ToolTier = ToolTier.FAST, schema: Dict = None):
        """
        装饰器：注册一个函数为工具
        """
        def decorator(func):
            # 如果没有提供 Schema，尝试自动生成 (这里简化处理，实际可能需要 Pydantic)
            tool_schema = schema if schema else cls._generate_default_schema(func)
            
            tool_def = ToolDefinition(
                name=name,
                description=description,
                func=func,
                tier=tier,
                schema=tool_schema
            )
            cls._tools[name] = tool_def
            print(f"[ToolRegistry] Registered tool: {name} ({tier.value})")
            return func
        return decorator

    @classmethod
    def get_tools(cls, tier: ToolTier = None) -> List[ToolDefinition]:
        """获取工具列表，可按 Tier 过滤"""
        if tier:
            return [t for t in cls._tools.values() if t.tier == tier and t.enabled]
        return list(cls._tools.values())

    @classmethod
    def get_tool(cls, name: str) -> ToolDefinition:
        return cls._tools.get(name)

    @classmethod
    def execute(cls, name: str, **kwargs) -> Any:
        """执行工具"""
        tool = cls._tools.get(name)
        if not tool:
            raise ValueError(f"Tool '{name}' not found.")
        
        try:
            # print(f"[ToolRegistry] Executing {name} with args: {kwargs}")
            return tool.func(**kwargs)
        except Exception as e:
            print(f"[ToolRegistry] Execution failed for {name}: {e}")
            return f"Error: {str(e)}"

    @staticmethod
    def _generate_default_schema(func) -> Dict:
        """
        简单的 Schema 生成器 (Placeholder)
        生产环境建议手动提供严谨的 JSON Schema
        """
        sig = inspect.signature(func)
        params = {}
        for k, v in sig.parameters.items():
            params[k] = {"type": "string", "description": f"Parameter {k}"}
            
        return {
            "type": "object",
            "properties": params,
            "required": list(params.keys())
        }

# 全局实例
tool_registry = ToolRegistry()
