# 项目架构概览 (Architecture Overview)

## 1. 核心架构模式 (Core Patterns)

本项目采用 **Driver-Navigator (驾驶员-领航员)** 双脑架构，辅以 **四维驱动 (Four-Dimensional Drive)** 心智模型，通过 **异步事件总线 (EventBus)** 进行解耦通信。

### 1.1 双脑架构 (Dual-Brain Architecture)

*   **F脑 (Fast Brain / Driver)**:
    *   **角色**: 驾驶员。
    *   **职责**: 负责实时交互、短期决策、具体行动执行。
    *   **模型**: Qwen (通义千问) / GLM-4。
    *   **特点**: 响应速度快，直接控制输出，拥有最终行动权。
    *   **输入**: 用户指令 + S脑建议 + 心智状态。

*   **S脑 (Slow Brain / Navigator)**:
    *   **角色**: 领航员。
    *   **职责**: 负责长期规划、深度分析、反思总结、代码自省。
    *   **模型**: DeepSeek-R1 (Reasoning Mode)。
    *   **特点**: 异步运行，不阻塞主线程，通过 `Suggestion Board` 提供建议，不直接干预行动。
    *   **能力**: 具备全项目代码扫描能力 (Prefix Caching)，能理解项目架构演进。

### 1.2 四维驱动心智 (4D Psyche Drive)

心智模块不再基于拟人化的情绪，而是基于控制论的 **认知稳态 (Cognitive Homeostasis)** 系统。核心由四个维度的数值驱动：

1.  **Curiosity (熵减)**: 追求信息的确定性，探索未知。
2.  **Interest (一致性)**: 维护逻辑与记忆的自洽，追求利益最大化。
3.  **Morality (对齐度)**: 拟合人类价值观与安全规范。
4.  **Fear (资源优化)**: 对算力、Token消耗及潜在风险的敏感度。

### 1.3 异步事件总线 (EventBus)

系统各组件通过 SQLite-backed EventBus 进行通信，实现时空解耦：
*   **Traceability**: 全链路 TraceID 追踪。
*   **Persistence**: 所有事件持久化存储，支持回溯分析。
*   **Observability**: 支持结构化日志与元数据 (Meta) 记录。

## 2. 系统数据流 (Data Flow)

1.  **用户输入**: 用户发送消息 -> `Driver` 接收。
2.  **F脑响应**: `Driver` 结合 `Memory` (短期+长期) 和 `Psyche` 状态 -> 生成回复 -> 发布 `driver_response` 事件。
3.  **S脑分析**: `Navigator` 周期性扫描 `EventBus` -> 获取最近交互历史 -> 结合全量代码上下文 -> 进行深度推理 (R1)。
4.  **状态更新**: S脑输出 `Suggestion` 和 `Psyche Delta` -> 更新 `Psyche` 四维状态 -> 影响下一轮 `Driver` 的 Prompt。
5.  **记忆固化**: S脑识别重要事实 -> 写入 `LongTerm Memory` (Vector + JSON)。

## 3. 目录结构 (Directory Structure)

```
src/
├── config/         # 配置中心 (Settings, Prompts)
├── core/           # 核心架构 (Driver, Navigator, Bus)
├── memory/         # 记忆系统 (ShortTerm, LongTerm, VectorDB)
├── psyche/         # 心智模块 (PsycheCore, 4D State)
├── tools/          # 工具体系 (Registry, Builtin Tools)
├── utils/          # 通用工具 (LLMClient, Helpers)
└── main.py         # 入口文件
```
