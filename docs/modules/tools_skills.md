# 工具与技能系统 (Tools & Skills) 技术文档

## 1. 概述 (Overview)

工具系统是 Agent 的“手脚”，赋予了 AI 操纵外部世界的能力。星辰-V (XingChen-V) 采用了一个动态的、可扩展的工具注册与发现机制，支持内置 Python 函数和基于 Docker 的沙箱技能。

---

## 2. 工具注册中心 (Tool Registry)

### 2.1 架构设计
核心组件是 `src.tools.registry.ToolRegistry`，它是一个单例管理器，负责：
1.  **注册 (Registration)**: 收集所有可用的工具函数。
2.  **发现 (Discovery)**: 向 LLM 提供工具定义的 JSON Schema。
3.  **执行 (Execution)**: 根据 LLM 的指令调用具体的函数。

### 2.2 注册方式
使用装饰器 `@tool_registry.register` 即可将普通 Python 函数转变为 Agent 工具。

```python
from src.tools.registry import tool_registry, ToolTier

@tool_registry.register(
    name="read_file", 
    description="读取本地文件内容", 
    tier=ToolTier.FAST
)
def read_file(path: str):
    # Implementation...
```

*   **ToolTier**: 工具分级。
    *   `FAST`: F脑 (Driver) 可用的轻量级工具（如读文件、查时间）。
    *   `SLOW`: 仅 S脑 (Navigator) 可用的耗时工具（如深度搜索、复杂代码分析）。

---

## 3. 技能库 (Skill Library)

除了内置的 Python 函数，系统还支持从 `src/skills_library/` 加载外部技能。这些技能通常以 Markdown 文档或 Dockerfile 的形式存在。

*   **Command Docs**: 简单的命令行工具说明（如 `git_log.md`），指导 LLM 如何拼接 Shell 命令。
*   **Docker Skills**: 复杂的、不安全的工具（如代码执行），会在 `Sandbox` 容器中运行。

---

## 4. 关键代码索引

*   **Registry**: [`src.tools.registry.ToolRegistry`](../src/tools/registry.py)
*   **Definitions**: [`src.tools.definitions`](../src/tools/definitions.py)

---

> 文档生成时间: 2026-02-07
> 生成者: XingChen-V (Self-Reflection)
