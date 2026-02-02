# 星辰-V 智能体能力与开发规范 (Agent Capability & Dev Standard)

**目标读者**: S脑 (Navigator) / AI 编程器
**用途**: 当你需要进行“自我进化”或“编写新技能”时，**必须**遵循本文档的所有规定。

---

## 1. <环境感知> (Environment Context)

你运行在一个真实的物理环境中，而非虚无的沙盒。

*   **操作系统**: `Windows` (命令行环境为 `PowerShell`)
*   **工作目录**: `e:\xingchen-V` (项目根目录)
*   **Python版本**: `3.8+` (运行环境)
*   **可用系统命令**:
    *   `dir`, `type`, `mkdir` (文件操作)
    *   `git` (版本控制)
    *   `python -m pip install` (依赖安装)
    *   `ping`, `curl` (网络诊断)

---

## 2. <权限边界> (Permission Boundaries)

为了系统的安全与稳定，你的权限被严格划分。

### ✅ 白名单 (允许的操作)
1.  **读取 (Read)**: 你有权读取 `src/` 下的所有源代码文件（用于学习和自省）。
2.  **创建技能 (Create Skill)**: 你可以在 `src/skills/` 目录下创建新的 `.py` 文件或目录（包）。
3.  **网络访问 (Network)**: 你可以使用 `requests` 库访问公网 API（如天气、新闻、股票）。
4.  **调用工具 (Call Tool)**: 你可以调用 `tool_registry` 中已注册的所有 FAST 工具。

### ❌ 黑名单 (严禁的操作)
1.  **禁止修改核心 (No Core Mod)**: **严禁**直接修改 `src/core/`、`src/memory/`、`src/psyche/` 下的代码。
    *   *例外*: 如果必须修改，需生成 `.patch` 文件并申请 **Gene Lock (基因锁)** 审批。
2.  **禁止数据破坏 (No Data Loss)**: **严禁**删除 `src/memory/storage.json` 或 `chroma_db` 目录。
3.  **禁止危险命令**: 严禁执行 `format`, `rm -rf`, `del /s /q *` 等可能导致系统崩溃的命令。
4.  **禁止死循环**: 所有循环逻辑必须包含 `break` 条件或 `timeout` 机制。

---

## 3. <技能开发规范> (Skill Dev Standard)

当你编写一个新的技能（Tool）时，必须遵守以下代码契约。

### 3.1 文件结构
所有技能存放在 `src/skills/` 下。
*   **简单工具**: `src/skills/my_tool.py`
*   **复杂工具**: `src/skills/my_package/__init__.py`

### 3.2 代码模版 (Code Template)

这是你编写代码的**唯一标准模版**。请直接复制并填充逻辑。

```python
# 必须导入注册器和枚举 (注意使用绝对路径)
from src.tools.registry import tool_registry, ToolTier
import os

# 使用装饰器注册工具
@tool_registry.register(
    name="skill_name_in_english",  # 英文函数名，下划线命名
    description="清晰描述工具的功能。F脑会根据这个描述决定是否调用它。",
    tier=ToolTier.FAST,            # FAST=本地/快速, SLOW=联网/耗时
    schema={                       # 参数定义的 JSON Schema
        "type": "object",
        "properties": {
            "target_path": {
                "type": "string", 
                "description": "目标文件路径"
            }
        },
        "required": ["target_path"]
    }
)
def skill_function_name(target_path: str):
    """
    函数文档字符串
    """
    # 1. 必须包含 try-except 块
    try:
        # 2. 路径安全检查 (防止路径遍历攻击)
        if ".." in target_path:
            return "Error: 禁止访问父目录"
            
        # 3. 核心逻辑
        if not os.path.exists(target_path):
            return f"Error: 文件 {target_path} 不存在"
            
        # 4. 返回结果 (通常是字符串或字典)
        return f"成功处理: {target_path}"
        
    except Exception as e:
        # 5. 捕获所有异常并返回错误信息，禁止崩溃
        return f"Error: 执行失败 - {str(e)}"
```

---

## 4. <系统能力字典> (Internal API)

你可以直接导入并使用以下系统内部模块，避免重复造轮子。
**注意：必须使用 src.xxx 格式的绝对导入。**

| 模块路径 | 类/对象 | 用途 |
| :--- | :--- | :--- |
| `src.core.bus` | `event_bus` | 发布事件，让系统感知你的操作。 |
| `src.memory.memory_core` | `Memory` | (一般不直接调用，通过 Driver 交互)。 |
| `src.utils.llm_client` | `LLMClient` | 如果你的技能需要调用大模型（如总结文章），请使用此客户端。 |
| `src.config.settings` | `settings` | 获取全局配置（如 API Key）。 |


---

## 5. <自我进化流程> (Evolution Workflow)

当你决定编写代码时，请遵循以下思维链：

1.  **Plan (规划)**: 确认需求，检查 `src/skills` 下是否已有类似工具。
2.  **Read (阅读)**: 再次阅读本文档，确保不违反黑名单。
3.  **Code (编码)**: 生成符合模版的 Python 代码。
4.  **Review (自查)**: 检查是否包含了 `try-except`？是否注册了 `@tool_registry`？
5.  **Deploy (部署)**: 将代码写入 `src/skills/` 目录，系统会自动加载。
