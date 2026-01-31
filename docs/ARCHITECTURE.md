# XingChen-V 架构设计文档

## 1. 核心设计理念：认知稳态与四维驱动

本项目不仅仅是一个简单的 LLM 包装器，而是试图模拟一个具备“心理状态”的智能体。
核心理论基于 **认知稳态 (Cognitive Homeostasis)**，即系统通过动态调整行为来维持内部状态的平衡。

驱动这一过程的是 **四维驱动 (Four-Dimensional Drive)** 模型：
- **Curiosity (好奇)**: 探索未知信息的欲望。
- **Interest (利益)**: 维护自身存在和记忆完整性的本能。
- **Morality (道德)**: 对齐人类价值观和社会规范的约束。
- **Fear (恐惧/资源)**: 对计算成本、风险和不确定性的规避。

---

## 2. 架构模式：Driver-Navigator (驾驶员-领航员)

为了解决 LLM 响应速度与深度思考之间的矛盾，我们采用了 **双脑架构**：

### 2.1 Driver (快脑/驾驶员)
- **位置**: `src/core/driver.py`
- **职责**: 
  - 负责与用户进行**实时**交互。
  - 拥有最终的**执行权**和**话语权**。
  - 它的思考过程是线性的、快速的，直接调用 LLM 生成回复。
- **特点**: 它是“前台”的代理人，性格傲娇，反应灵敏。

### 2.2 Navigator (慢脑/领航员)
- **位置**: `src/core/navigator.py`
- **职责**:
  - 在后台**异步**运行（目前模拟中）。
  - 负责**长期规划**、**深度分析**和**反思**。
  - 它不直接控制身体（不直接输出），而是通过 **Suggestion Board (建议板)** 向 Driver 提供建议。
- **交互**: Driver 在空闲时会查看 Suggestion Board，决定是否采纳建议。

### 2.3 Psyche (心智/情感引擎)
- **位置**: `src/psyche/psyche_core.py`
- **职责**:
  - 维护上述“四维驱动”的数值状态。
  - 将数值状态转化为自然语言的 **Prompt Modifier (提示词修饰符)**。
  - **数据流**: User Input -> Update Psyche State -> Generate Modifier -> Inject into Driver's System Prompt.

---

## 3. 系统逻辑流 (Workflow)

当用户输入一条消息时，系统的数据流向如下：

1.  **感知 (Perception)**: 
    - `main.py` 接收用户输入。
    - 未来 Auditor 模块会在此处记录原始日志。

2.  **心智影响 (Psyche Influence)**:
    - `Psyche` 模块根据当前状态，生成修饰词（如“表现出极强的好奇心”或“变得非常谨慎”）。
    - 这个修饰词会被注入到 Driver 的 System Prompt 中，改变它的“潜意识”态度。

3.  **快脑反应 (Driver Reaction)**:
    - `Driver` 接收用户输入 + 心智修饰词。
    - `Driver` 调用 `LLMClient` (支持 DeepSeek/Zhipu/Qwen) 进行推理。
    - 生成回复并输出给用户。

4.  **慢脑规划 (Navigator Planning)** (异步/TODO):
    - `Navigator` 分析对话历史，更新长期记忆或调整策略。
    - 如果发现问题，会在 Suggestion Board 上留言，等待 Driver 下次读取。

---

## 4. 基础设施

- **统一 LLM 客户端**: `src/utils/llm_client.py` 封装了不同厂商的 API 差异，实现了单例模式，支持通过 `.env` 快速切换模型。
- **环境管理**: `.env` 文件管理敏感 Key，`check_env.py` 确保运行环境合规。

---

*文档生成时间: 2026-01-31*
