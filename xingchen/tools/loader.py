import importlib
from xingchen.utils.logger import logger

def load_all_tools():
    """
    加载所有内置工具，触发 ToolRegistry 注册
    """
    tool_modules = [
        "xingchen.tools.builtin.web_tools",
        "xingchen.tools.builtin.system_tools"
    ]
    
    logger.info("[ToolLoader] Loading built-in tools...")
    for module_name in tool_modules:
        try:
            importlib.import_module(module_name)
            logger.info(f"[ToolLoader] Imported {module_name}")
        except Exception as e:
            logger.error(f"[ToolLoader] Failed to import {module_name}: {e}", exc_info=True)
