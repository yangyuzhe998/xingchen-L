
import subprocess
from datetime import datetime
from src.tools.registry import ToolRegistry
from src.tools.definitions import ToolTier
from src.core.library_manager import library_manager

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

@ToolRegistry.register(
    name="run_shell_command",
    description="在系统终端执行 Shell 命令 (Windows PowerShell)。请谨慎使用。",
    tier=ToolTier.FAST,
    schema={
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "要执行的命令"}
        },
        "required": ["command"]
    }
)
def run_shell_command(command: str):
    print(f"Executing shell command: {command}")
    try:
        # 使用 powershell 执行
        result = subprocess.run(["powershell", "-Command", command], capture_output=True, text=True, timeout=30)
        output = result.stdout
        if result.stderr:
            output += f"\nError: {result.stderr}"
        if not output:
             output = "(No output)"
        return output[:1000] # 限制输出长度
    except Exception as e:
        return f"Execution failed: {e}"

@ToolRegistry.register(
    name="search_skills",
    description="在技能图书馆中搜索相关技能。",
    tier=ToolTier.FAST,
    schema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "搜索关键词或问题描述"}
        },
        "required": ["query"]
    }
)
def search_skills(query: str):
    skills = library_manager.search_skills(query)
    if not skills:
        return "未找到相关技能。"
    
    result = "找到以下相关技能:\n"
    for s in skills:
        result += f"- ID: {s['id']}\n  Name: {s['name']}\n  Description: {s['description']}\n  Path: {s['path']}\n"
    return result

@ToolRegistry.register(
    name="read_skill",
    description="读取特定技能的详细内容 (SKILL.md)。",
    tier=ToolTier.FAST,
    schema={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "技能文件的路径 (从 search_skills 获取)"}
        },
        "required": ["path"]
    }
)
def read_skill(path: str):
    return library_manager.checkout_skill(path)
