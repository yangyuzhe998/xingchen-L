# 接口协议文档 (API Protocols)

## 1. 概述 (Overview)

本文档定义了星辰-V (XingChen-V) 系统内部组件交互的数据格式，以及前后端（UI 与 Core）通信的标准接口。

所有的事件和数据交互均基于 **Pydantic V2** 模型进行强类型验证。

---

## 2. 事件总线协议 (Event Bus Protocol)

所有通过 `EventBus` 流转的消息必须继承自 `BaseEvent`。

### 2.1 基础事件结构 (`BaseEvent`)

```json
{
  "id": 1,
  "trace_id": "uuid-v4-string",
  "timestamp": 1700000000.0,
  "type": "event_type_enum",
  "source": "component_name",
  "payload": { ... },
  "meta": { ... }
}
```

*   **type**: 事件类型 (`EventType` 枚举)。
*   **payload**: 核心数据负载，根据 type 不同而变化。
*   **meta**: 附加元数据（如耗时、Token 消耗、情绪标签）。

### 2.2 核心事件类型

| 事件类型 (`type`) | 触发源 (`source`) | Payload 结构 | 说明 |
| :--- | :--- | :--- | :--- |
| `user_input` | UI / User | `{"content": "用户说的话"}` | 用户发送消息时触发 |
| `driver_response` | Driver | `{"content": "AI的回复"}` | F脑生成回复后触发 |
| `navigator_suggestion` | Navigator | `{"content": "建议内容"}` | S脑产生指导意见时触发 |
| `system_notification` | Memory / System | `{"type": "memory_full", "count": 20}` | 系统级通知（如内存满） |
| `proactive_instruction` | Psyche / Navigator | `{"content": "主动发言指令"}` | 触发 F脑 主动行为 |

---

## 3. UI 交互接口 (UI Interface)

前端界面必须实现 `src.interfaces.ui_interface.UserInterface` 定义的抽象方法。

### 3.1 协议定义

```python
class UserInterface:
    def display_message(self, role: str, content: str, meta: Dict = None):
        """显示消息"""
        pass

    def set_input_handler(self, handler: Callable[[str], None]):
        """注册输入回调"""
        pass

    def update_status(self, status: str, details: Dict = None):
        """更新状态栏"""
        pass
```

### 3.2 角色定义 (`role`)
*   `user`: 用户。
*   `assistant`: 星辰-V (通常指 Driver 的输出)。
*   `system`: 系统提示或内心独白 (Thought Chain)。

---

## 4. 关键代码索引

*   **Event Schemas**: [`src.schemas.events`](../src/schemas/events.py)
*   **UI Interface**: [`src.interfaces.ui_interface`](../src/interfaces/ui_interface.py)

---

> 文档生成时间: 2026-02-07
> 生成者: XingChen-V (Self-Reflection)
