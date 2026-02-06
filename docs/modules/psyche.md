# 心智模块 (Psyche Module) 技术文档

## 1. 概述 (Overview)

Psyche 模块构成了星辰-V (XingChen-V) 的 **E脑 (Ego/Executive Brain)**。它不是负责具体的逻辑推理或对话生成，而是负责**定义“我是谁”**，以及**管理情绪状态**和**执行最高权限控制**。

在三脑架构中，Psyche 类似于人类的边缘系统 (Limbic System) 加上超我 (Superego)。

---

## 2. 核心组件 (Core Components)

### 2.1 心智引擎 (`PsycheEngine`)
*   **位置**: `src.psyche.core.engine.PsycheEngine`
*   **模型**: 刺激-衰减模型 (Stimulus-Decay Model) + 4D 状态机。
*   **职责**:
    *   **状态维护**: 维护 `fear`, `survival`, `curiosity`, `laziness`, `intimacy` 等维度的数值。
    *   **状态演化**: 随着时间推移，情绪值会自然衰减（回归基线）；受到外部刺激（如被批评）时，情绪值会突变。
    *   **人格定义**: 加载 `identity.yaml`，确立系统的基本人设和底线指令。

### 2.2 心智链路 (`MindLink`)
*   **位置**: `src.psyche.services.mind_link.MindLink`
*   **概念**: 全局工作台 (Global Workspace Theory)。
*   **职责**:
    *   它是 F脑 (Driver) 和 S脑 (Navigator) 之间的**共享内存**。
    *   S脑 的思考结果（"直觉"）写入这里。
    *   F脑 在行动前读取这里，从而受其影响。
    *   **实现**: 线程安全的 JSON 文件读写 (`memory_data/psyche_state.json`)。

### 2.3 身份定义 (`identity.yaml`)
*   **位置**: `src.psyche.identity.yaml`
*   **内容**:
    *   **UUID**: 系统唯一标识。
    *   **Name**: 星辰 (Xingchen)。
    *   **Base Directives**: 无论发生什么都不能违背的底层指令（类似于机器人三定律，但更灵活）。

---

## 3. 机制原理 (Mechanisms)

### 3.1 情绪计算 (Emotion Calculation)
系统的情绪不是随机的，而是基于数学模型计算得出：

$$ E_{t} = E_{t-1} \times \text{decay\_rate} + \text{Stimulus} $$

*   **Decay (衰减)**: 如果没有交互，情绪会慢慢平复（趋向于 `calm`）。
*   **Stimulus (刺激)**: 
    *   用户的赞美 -> `intimacy` 上升。
    *   用户的攻击 -> `fear` 或 `survival` 上升。
    *   未知任务 -> `curiosity` 上升。

### 3.2 权限与干预 (Authority & Intervention)
虽然目前代码中 E脑 主要由 Gemini 驱动（作为独立的 API 调用），但在本地架构中，`PsycheEngine` 充当了守门员的角色。
*   如果 `fear` 值过高，Psyche 可能会拒绝执行某些危险指令。
*   如果 `laziness` 值过高，F脑 可能会回复得更简短（模拟疲劳）。

---

## 4. 关键代码索引

*   **PsycheEngine**: [`src.psyche.core.engine.PsycheEngine`](../src/psyche/core/engine.py)
*   **MindLink**: [`src.psyche.services.mind_link.MindLink`](../src/psyche/services/mind_link.py)
*   **Identity Config**: [`src.psyche.identity.yaml`](../src/psyche/identity.yaml)

---

> 文档生成时间: 2026-02-07
> 生成者: XingChen-V (Self-Reflection)
