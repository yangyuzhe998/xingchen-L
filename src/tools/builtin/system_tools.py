
import subprocess
import os
from datetime import datetime
from src.tools.registry import ToolRegistry
from src.tools.definitions import ToolTier
from src.core.managers.library_manager import library_manager
from src.utils.logger import logger

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
    logger.info(f"[SystemTools] Executing shell command: {command}")
    print(f"Executing shell command: {command}")
    try:
        # 使用 powershell 执行
        result = subprocess.run(["powershell", "-Command", command], capture_output=True, text=True, timeout=30)
        output = result.stdout
        if result.stderr:
            output += f"\nError: {result.stderr}"
        if not output:
             output = "(No output)"
        
        logger.info(f"[SystemTools] Command finished. Output len: {len(output)}")
        return output[:1000] # 限制输出长度
    except Exception as e:
        logger.error(f"[SystemTools] Command failed: {e}", exc_info=True)
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
    # Security check: must be within skills_library
    if "skills_library" not in path:
        return "Error: Access denied. Can only read files within skills_library."
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading skill file: {e}"

@ToolRegistry.register(
    name="read_document",
    description="[深度阅读] 读取本地文档内容 (支持 Markdown/Text)。用于 S-Brain 深入分析抓取到的知识。",
    tier=ToolTier.SLOW,
    schema={
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "文件的绝对路径"},
            "start_line": {"type": "integer", "description": "起始行号 (默认0)", "default": 0},
            "end_line": {"type": "integer", "description": "结束行号 (默认2000)", "default": 2000}
        },
        "required": ["file_path"]
    }
)
def read_document(file_path: str, start_line: int = 0, end_line: int = 2000):
    """
    读取文件内容，模拟 '上传文件' 给 LLM
    """
    if not os.path.exists(file_path):
        return f"Error: File not found at {file_path}"
    
    # 简单的安全检查，防止读取系统关键文件
    # 在生产环境中需要更严格的 Sandboxing
    allowed_extensions = ['.md', '.txt', '.log', '.json', '.yaml', '.py']
    if not any(file_path.endswith(ext) for ext in allowed_extensions):
        return f"Error: Unsupported file type. Allowed: {allowed_extensions}"

    try:
        logger.info(f"[SystemTools] Reading document: {file_path} (Lines: {start_line}-{end_line})")
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        total_lines = len(lines)
        if start_line >= total_lines:
            return "Error: start_line exceeds total lines."
            
        selected_lines = lines[start_line:end_line]
        content = "".join(selected_lines)
        
        return (
            f"📄 File: {os.path.basename(file_path)}\n"
            f"📊 Lines: {start_line} - {min(end_line, total_lines)} (of {total_lines})\n"
            f"----------------------------------------\n"
            f"{content}"
        )
    except Exception as e:
        logger.error(f"[SystemTools] Read document failed: {e}", exc_info=True)
        return f"Error reading file: {e}"
def read_skill(path: str):
    return library_manager.checkout_skill(path)
