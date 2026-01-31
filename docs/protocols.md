# 接口协议文档 (Interface Protocols)

## 1. 事件总线协议 (EventBus Protocol)

所有模块间的通信必须遵循 `Event` 数据类定义。

### 数据结构 (Data Structure)

```python
@dataclass
class Event:
    type: str          # 事件类型 (e.g., "user_input", "driver_response")
    source: str        # 事件源 (e.g., "user", "driver", "navigator")
    payload: Dict      # 核心数据载荷
    meta: Dict         # 元数据 (TraceID, Emotion, Thoughts)
    trace_id: str      # 全链路追踪 ID (UUID)
    timestamp: float   # Unix 时间戳
    id: Optional[int]  # 数据库自增 ID (读取时存在)
```

### 标准事件类型 (Standard Event Types)

| Type | Source | Payload | Meta |
| :--- | :--- | :--- | :--- |
| `user_input` | `user` | `{"content": "..."}` | `{}` |
| `driver_response` | `driver` | `{"content": "..."}` | `{"inner_voice": "...", "psyche_state": "..."}` |
| `psyche_update` | `navigator` | `{"delta": {...}}` | `{"reasoning": "..."}` |

---

## 2. 工具注册协议 (Tool Registry Protocol)

工具开发必须使用装饰器模式进行注册，并明确指定 Tier。

### 注册装饰器 (Decorator)

```python
@ToolRegistry.register(
    name="tool_name", 
    description="Tool description", 
    tier=ToolTier.FAST,  # FAST (同步/F脑) 或 SLOW (异步/S脑)
    schema={...}         # Optional JSON Schema
)
def my_tool(arg1: str):
    pass
```

### 工具分级 (Tool Tiers)

*   **FAST**: 耗时短，无副作用或副作用可控，供 `Driver` 实时调用。
*   **SLOW**: 耗时长，涉及复杂逻辑或高风险操作，供 `Navigator` 规划使用。

---

## 3. LLM 客户端协议 (LLM Client Protocol)

统一的 LLM 调用接口，支持多供应商切换与链路追踪。

### 接口定义 (Interface)

```python
class LLMClient:
    def __init__(self, provider="default"):
        # provider: "deepseek" | "qwen" | "zhipu" | "default"
        pass

    def chat(self, messages: List[Dict], temperature=0.7, trace_id=None) -> str:
        """
        messages: Standard OpenAI format [{"role": "user", "content": "..."}]
        trace_id: 用于日志追踪
        """
        pass
```

### 环境变量规范 (.env)

*   `DEEPSEEK_API_KEY` / `DEEPSEEK_BASE_URL`
*   `QWEN_API_KEY` / `QWEN_BASE_URL`
*   `ZHIPU_API_KEY` / `ZHIPU_BASE_URL`
