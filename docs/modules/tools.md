# 工具模块详解 (Tools Module)

## 1. 工具注册中心 (Tool Registry)

`src/tools/registry.py`

采用单例模式 + 装饰器模式管理所有工具。

### 使用方法

```python
from tools.registry import ToolRegistry, ToolTier

@ToolRegistry.register("tool_name", "Description", tier=ToolTier.FAST)
def my_function(arg):
    ...
```

## 2. 工具分级 (Tiers)

系统根据工具的执行成本和风险进行分级：

| Tier | 描述 | 适用场景 | 执行者 |
| :--- | :--- | :--- | :--- |
| **FAST** | 快速、低风险、只读或轻量写入 | 获取时间、计算、简单查询 | Driver |
| **SLOW** | 耗时、高风险、复杂I/O | 深度搜索、大规模文件操作、代码重构 | Navigator |

## 3. 内置工具 (Builtin Tools)

`src/tools/builtin/`

*   `get_current_time`: 获取当前系统时间。
*   `calculate`: 数学表达式计算。
*   (待扩展): 文件读写、网络请求等。
