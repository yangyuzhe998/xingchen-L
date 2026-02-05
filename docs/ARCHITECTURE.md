# XingChen-V 系统架构文档

> 文档版本: v2.0.0
> 最后更新: 2026-02-05

本文档详细描述了 XingChen-V 的核心架构、双脑协同机制以及数据流向，旨在帮助开发者理解系统的内部运作逻辑。

## 1. 核心架构：双脑异步协同 (Dual-Brain Async Topology)

XingChen-V 的核心设计哲学是**模拟生物大脑**的运作模式，将“快思考”和“慢思考”分离，通过异步机制进行协作。

### 1.1 F-Brain (Driver) - 快脑/显意识
*   **角色**: 前台接待员，负责实时交互。
*   **模型**: Qwen-Max (通义千问)。
*   **特点**: 响应速度快 (秒级)，但逻辑深度有限，依赖短期记忆。
*   **职责**:
    *   接收用户输入 (CLI/Web)。
    *   读取心智状态 (Psyche) 和直觉 (MindLink)。
    *   检索短期记忆和部分长期记忆。
    *   调用工具 (Tools)。
    *   生成回复并广播到事件总线。

### 1.2 S-Brain (Navigator) - 慢脑/潜意识
*   **角色**: 后台分析师，负责深度思考。
*   **模型**: DeepSeek-Reasoner (R1)。
*   **特点**: 思考慢 (分钟级)，擅长逻辑推演、记忆整理和模式识别。
*   **职责**:
    *   监听事件总线 (EventBus)。
    *   周期性触发 (Cycle Trigger)。
    *   提炼事实、撰写日记、构建图谱。
    *   向 F-Brain 注入“直觉” (Intuition) 和“情绪波动” (Psyche Delta)。
    *   生成“主动干预指令” (Proactive Instruction)。

### 1.3 EventBus - 神经网络
*   **角色**: 消息中枢。
*   **机制**: 发布-订阅 (Pub/Sub) 模式。
*   **作用**: 解耦 F-Brain 和 S-Brain，确保两者互不阻塞。

---

## 2. 数据流向 (Data Flow)

### 2.1 交互链路 (Interaction Chain)
当用户输入一条消息时：

1.  **Input**: 用户输入 -> `WebApp` / `CLI`。
2.  **Dispatch**: 消息被传递给 `Driver.think()`。
3.  **Context Assembly**: `Driver` 收集上下文：
    *   `Psyche`: 当前心情指数。
    *   `MindLink`: 潜意识的最新建议。
    *   `Memory`: 短期对话历史 + 长期记忆检索 (RAG)。
4.  **LLM Inference**: 组装 Prompt -> 调用 LLM -> 获取回复。
5.  **Output**: 回复展示给用户。
6.  **Broadcast**: `Driver` 将 `(User Input, Assistant Reply)` 打包发布到 `EventBus`。

### 2.2 记忆链路 (Memory Chain)
记忆是如何形成和沉淀的：

1.  **Buffer**: `Driver` 将对话存入 `ShortTermMemory` (内存列表)。
2.  **Trigger**: `CycleManager` 监控到对话轮数达到阈值 (如 5 轮) 或长时间空闲。
3.  **Analysis**: `CycleManager` 唤醒 `Navigator` (S-Brain)。
4.  **Processing**: `Navigator` 读取最近的对话记录，进行深度分析：
    *   **Fact Extraction**: 提取结构化事实 -> `JsonStorage`。
    *   **Diary Generation**: 生成叙事日记 -> `DiaryStorage` (Markdown)。
    *   **Graph Building**: 提取实体关系 -> `GraphMemory` (JSON)。
5.  **Compression**: 分析完成后，`Navigator` 清空 `ShortTermMemory`，完成“记忆压缩”。

### 2.3 心智演化链路 (Psyche Evolution Chain)
情绪是如何变化的：

1.  **Stimulus**: 每次用户交互或 S-Brain 的思考，都会产生一个 `Delta` (变化量)。
2.  **Update**: `PsycheEngine` 接收 `Delta`，更新四维参数 (Fear, Survival, Curiosity, Laziness)。
3.  **Decay**: `CycleManager` 会随时间推移，自动让情绪参数向基准值衰减 (Time Decay)。
4.  **Feedback**: 更新后的心智状态会实时影响 `Driver` 的 Prompt，从而改变回复的语气。

---

## 3. 模块依赖图 (Topology)

```
[User Interface] (Web/CLI)
       |
       v
[Driver (F-Brain)] <----(Read)---- [Memory Facade]
       |                                  ^
       | (Publish Event)                  | (Write/Compact)
       v                                  |
[EventBus (SQLite)] ----------------> [Navigator (S-Brain)]
       ^                                  |
       | (Trigger)                        | (Update State)
       |                                  v
[CycleManager] -----------------> [Psyche Engine]
                                          |
                                          v
                                    (Inject Intuition)
                                          |
                                    [Driver Prompt]
```
