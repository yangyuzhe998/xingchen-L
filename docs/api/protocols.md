# 星辰-V (XingChen-V) 接口协议文档

## 1. 概述
本文档定义了星辰-V 系统内部各组件之间的通信协议，以及与外部（用户、MCP工具）的交互规范。

## 2. Event Bus (事件总线) 协议
核心通信机制，基于 SQLite 实现的持久化队列。

### 2.1 事件结构 (Schema)
所有事件必须遵循以下 JSON 结构：
```json
{
  "trace_id": "uuid-v4",       // 追踪ID，用于全链路追踪
  "type": "event_type",        // 事件类型（见下文）
  "source": "component_name",  // 来源组件 (driver, navigator, user, system)
  "payload": {},               // 核心数据载荷
  "meta": {                    // 元数据
    "timestamp": 1700000000,
    "psyche_state": {...}      // 当时的心智状态快照
  }
}
```

### 2.2 核心事件类型
| 事件类型 (type) | 来源 (source) | 说明 | Payload 示例 |
|---|---|---|---|
| `user_input` | user | 用户输入 | `{"content": "你好"}` |
| `driver_response` | driver | F脑回复 | `{"content": "你好呀", "inner_voice": "..."}` |
| `navigator_suggestion` | navigator | S脑建议 | `{"suggestion": "用户似乎很疲惫...", "intent": "comfort"}` |
| `psyche_update` | psyche | 心智状态变更 | `{"delta": {"joy": 0.1}, "reason": "user_praise"}` |
| `system_notification` | system | 系统通知 | `{"level": "info", "message": "记忆归档完成"}` |

## 3. 双脑交互协议

### 3.1 F-Brain (Driver) -> User
F脑负责直接与用户交互。
- **输入**: `user_input` + `navigator_suggestion` (Optional)
- **输出**: JSON 格式
```json
{
  "reply": "用户可见的回复文本",
  "inner_voice": "F脑的内心独白（不可见）",
  "emotion": "neutral" // 当前情绪标签
}
```

### 3.2 S-Brain (Navigator) -> System
S脑不直接回复用户，而是生成“潜意识流”。
- **触发机制**: CycleManager (基于轮数/情绪/空闲)
- **输出**:
```json
{
  "suggestion": "对F脑的战术指导",
  "psyche_delta": {"curiosity": 0.1}, // 情绪修正
  "memory_archival": true, // 是否触发记忆归档
  "evolution_request": "need_python_tool" // 是否触发进化
}
```

## 4. MCP (Model Context Protocol) 接口
星辰-V 使用 MCP 协议来扩展工具能力。

### 4.1 配置文件
位置: `src/config/mcp_config.json`
```json
{
  "mcpServers": {
    "puppeteer": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-puppeteer"]
    }
  }
}
```

### 4.2 工具调用 (Tool Use)
F脑通过 OpenAI Function Calling 格式调用 MCP 工具。
- **Request**:
```json
{
  "name": "puppeteer_navigate",
  "arguments": {"url": "https://github.com"}
}
```
- **Response**: 标准 MCP 响应格式（Text/Image）。

## 5. 记忆存储协议

### 5.1 向量数据库 (ChromaDB)
- **Collection**: `long_term_memory`
- **Metadata**:
  - `type`: "fact" | "episode" | "skill"
  - `timestamp`: Unix timestamp
  - `tags`: ["python", "coding"]

### 5.2 结构化存储 (JSON)
- **File**: `src/memory_data/storage.json`
- **Schema**:
```json
{
  "user_profile": {"name": "...", "preferences": {...}},
  "system_state": {"version": "1.0", "boot_count": 42}
}
```
