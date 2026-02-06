# 核心模块 (Core Module) 技术文档

## 1. 概述 (Overview)

Core 模块是星辰-V (XingChen-V) 的中枢神经系统，负责协调双脑（F脑与S脑）、管理系统生命周期、调度事件总线以及执行具体的技能工具。它实现了 System 1 (快思考) 和 System 2 (慢思考) 的工程化落地。

---

## 2. 架构拓扑 (Architecture Topology)

系统采用 **Tri-Brain (三脑) 架构**，但在 Core 模块中主要体现为 F脑与S脑的协作，以及通过 E脑 (Psyche) 施加影响。

### 2.1 核心组件

1.  **F脑 - 驾驶员 (`Driver`)**
    *   **位置**: `src.core.driver.engine.Driver`
    *   **模型**: Qwen (通义千问)
    *   **职责**:
        *   **实时交互**: 直接处理用户的输入，生成回复。
        *   **短期决策**: 决定是否调用工具、是否查询记忆。
        *   **特点**: 响应速度快，单线程同步运行（主循环）。
    
2.  **S脑 - 领航员 (`Navigator`)**
    *   **位置**: `src.core.navigator.core.Navigator`
    *   **模型**: DeepSeek (R1 推理模式)
    *   **职责**:
        *   **深度思考**: 在后台异步分析对话脉络、用户意图。
        *   **记忆整理**: 负责压缩短期记忆、生成日记、更新知识图谱。
        *   **直觉注入**: 通过 `MindLink` 将思考结果注入 F脑 的潜意识。
    *   **组件**:
        *   `Compressor`: 记忆压缩器。
        *   `Reasoner`: 深度推理机。
        *   `ContextManager`: 上下文组装器。
    
3.  **事件总线 (`EventBus`)**
    *   **位置**: `src.core.bus.event_bus.SQLiteEventBus`
    *   **机制**: 基于 SQLite 的持久化发布/订阅模型。
    *   **职责**: 解耦 F脑、S脑、记忆模块。所有关键动作（如 `user_input`, `driver_response`, `system_notification`）都作为事件在总线上流转。

4.  **周期管理器 (`CycleManager`)**
    *   **位置**: `src.core.managers.cycle.manager.CycleManager`
    *   **职责**: 监控系统状态，触发 S脑 的活动。
    *   **触发器 (`Triggers`)**:
        *   `MessageCountTrigger`: 对话达到一定轮数触发 S脑。
        *   `IdleTrigger`: 系统空闲时触发 S脑 整理记忆。
        *   `EmotionTrigger`: 情绪波动大时触发 S脑 反思。
        *   `MemoryFullTrigger`: 短期记忆满时触发压缩。

5.  **进化管理器 (`EvolutionManager`)**
    *   **位置**: `src.core.managers.evolution_manager.EvolutionManager`
    *   **职责**: 负责系统的自我进化，支持搜索 MCP Server 或生成 Python 代码来扩展能力。

6.  **沙箱环境 (`Sandbox`)**
    *   **位置**: `src.core.managers.sandbox.Sandbox`
    *   **职责**: 基于 Docker 容器运行不信任的生成代码，保障宿主机安全。

---

## 3. 工作流 (Workflows)

### 3.1 对话交互流程 (The Dual-Process Loop)

1.  **用户输入**: 用户发送消息。
2.  **事件发布**: `UserInputPayload` 被发布到 `event_bus`。
3.  **F脑响应**: `Driver` 接收事件，结合当前上下文 (`Context`) 和潜意识 (`MindLink`)，调用 LLM 生成回复。
4.  **S脑旁观**: `CycleManager` 监听对话，如果满足触发条件（如每 5 轮），则激活 `Navigator`。
5.  **异步推理**: `Navigator` 在后台线程启动 DeepSeek，分析刚才的对话，提取知识或修正 F脑 的行为策略。
6.  **直觉注入**: `Navigator` 将分析结果写入 `MindLink`。
7.  **闭环**: 下一次 F脑 生成回复时，会读取 `MindLink` 中的新直觉，从而体现出“反思”后的行为变化。

### 3.2 记忆压缩流程

1.  `Memory` 检测到短期记忆条目超过阈值（如 20 条）。
2.  发布 `memory_full` 事件。
3.  `MemoryFullTrigger` 捕获事件，调用 `Navigator.compress_memory()`。
4.  `Compressor` 组件将最近的对话总结为摘要 (Summary) 和事实 (Facts)。
5.  摘要存入长期记忆，事实存入知识图谱。
6.  清空短期记忆缓存。

---

## 4. 关键代码索引

*   **Driver**: [`src.core.driver.engine.Driver`](../src/core/driver/engine.py)
*   **Navigator**: [`src.core.navigator.core.Navigator`](../src/core/navigator/core.py)
*   **EventBus**: [`src.core.bus.event_bus.SQLiteEventBus`](../src/core/bus/event_bus.py)
*   **CycleManager**: [`src.core.managers.cycle.manager.CycleManager`](../src/core/managers/cycle/manager.py)
*   **EvolutionManager**: [`src.core.managers.evolution_manager.EvolutionManager`](../src/core/managers/evolution_manager.py)
*   **Sandbox**: [`src.core.managers.sandbox.Sandbox`](../src/core/managers/sandbox.py)

---

> 文档生成时间: 2026-02-07
> 生成者: XingChen-V (Self-Reflection)
