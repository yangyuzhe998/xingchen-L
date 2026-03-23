from typing import Dict, List, Any, Callable, Optional
import inspect
from .definitions import ToolDefinition, ToolTier
from xingchen.utils.logger import logger
from xingchen.utils.proxy import lazy_proxy


class ToolRegistry:
    """
    工具注册中心 (Singleton)
    管理所有的 Agent 工具，支持按 Tier (Fast/Slow)过滤。
    """
    _instance = None
    _tools: Dict[str, ToolDefinition] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ToolRegistry, cls).__new__(cls)
        return cls._instance

    @classmethod
    def register(cls, name: str, description: str, tier: ToolTier = ToolTier.FAST, schema: Dict = None):
        """装饰器：注册一个函数为工具"""
        def decorator(func):
            tool_schema = schema if schema else cls._generate_default_schema(func)
            
            tool_def = ToolDefinition(
                name=name,
                description=description,
                func=func,
                tier=tier,
                schema=tool_schema
            )
            cls._tools[name] = tool_def
            logger.info(f"[ToolRegistry] Registered tool: {name} ({tier.value})")
            return func
        return decorator

    @classmethod
    def get_tools(cls, tier: ToolTier = None) -> List[ToolDefinition]:
        """获取工具列表，可按 Tier 过滤"""
        if tier:
            return [t for t in cls._tools.values() if t.tier == tier and t.enabled]
        return list(cls._tools.values())

    @classmethod
    def get_openai_tools(cls, tier: ToolTier = None) -> List[Dict]:
        """获取 OpenAI 格式的工具定义列表"""
        tools = cls.get_tools(tier)
        openai_tools = []
        for t in tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.schema
                }
            })
        return openai_tools

    @classmethod
    def get_tool(cls, name: str) -> Optional[ToolDefinition]:
        return cls._tools.get(name)

    @classmethod
    def execute(cls, name: str, **kwargs) -> Any:
        """执行工具"""
        tool = cls._tools.get(name)
        if not tool:
            raise ValueError(f"Tool '{name}' not found.")
        
        try:
            return tool.func(**kwargs)
        except Exception as e:
            logger.error(f"[ToolRegistry] Execution failed for {name}: {e}", exc_info=True)
            return f"Error: {str(e)}"

    @staticmethod
    def _generate_default_schema(func) -> Dict:
        """简单的 Schema 生成器"""
        sig = inspect.signature(func)
        params = {}
        for k, v in sig.parameters.items():
            params[k] = {"type": "string", "description": f"Parameter {k}"}
            
        return {
            "type": "object",
            "properties": params,
            "required": list(params.keys())
        }


_tool_registry_instance: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """获取全局 ToolRegistry 实例（延迟初始化）。"""
    global _tool_registry_instance
    if _tool_registry_instance is None:
        _tool_registry_instance = ToolRegistry()
    return _tool_registry_instance


tool_registry = lazy_proxy(get_tool_registry, ToolRegistry)
