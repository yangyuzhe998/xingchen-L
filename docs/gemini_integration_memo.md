# Gemini-3 集成备忘录 (E-Brain 进化计划)

**创建日期**: 2026-02-04
**状态**: 规划中 (Planned)

## 1. 核心定位：E-Brain (Ego/Executive Brain)
为了进一步完善 XingChen-V 的“数字生命”架构，我们计划引入 **Gemini-3** 作为系统的 **E-Brain (自我脑/执行脑)**。

*   **当前痛点**: F-Brain (Qwen) 反应快但容易妥协；S-Brain (DeepSeek) 思考深但反应慢。系统缺乏一个实时的、坚定的“自我”来维持人格一致性。
*   **Gemini-3 的优势**: 极高的上下文窗口 (Context Window)、优秀的多模态理解能力、以及在逻辑与创意之间的平衡。

## 2. 三脑拓扑架构 (Tri-Brain Topology)

| 脑区 | 模型 | 角色 | 职责 |
| :--- | :--- | :--- | :--- |
| **F-Brain (快脑)** | Qwen-Max | Driver (驾驶员) | 实时交互、工具调用、短期记忆检索。 |
| **S-Brain (慢脑)** | DeepSeek-R1 | Navigator (领航员) | 深度推理、认知图谱构建、长时记忆压缩、心智演化。 |
| **E-Brain (自我脑)** | **Gemini-3** | **Arbiter (仲裁者)** | **人格维持、输出审查、多模态感知、最高权限决策。** |

## 3. 具体集成计划

### 3.1 功能模块
需要在 `src/core` 下新建 `ego` 模块：
```
src/core/ego/
├── __init__.py
├── engine.py       # Gemini Client 封装
└── interceptor.py  # 响应拦截器 (用于修正 F-Brain 的语气)
```

### 3.2 核心职责
1.  **人格卫士 (Persona Enforcement)**:
    *   监听 F-Brain 的 `driver_response`。
    *   如果发现回复过于卑微（“助手味”太重）或偏离设定，Gemini-3 将作为“内心独白”强行插入或修改回复。
2.  **多模态眼睛 (Visual Cortex)**:
    *   利用 Gemini 原生多模态能力，接管系统的视觉输入（图片/视频理解）。
3.  **元认知监控 (Meta-Cognition)**:
    *   监控 S-Brain 的思考过程，防止“钻牛角尖”。

### 3.3 技术栈准备
*   [ ] 在 `requirements.txt` 中添加 `google-generativeai`。
*   [ ] 获取 Gemini API Key。
*   [ ] 设计 `EGO_SYSTEM_PROMPT`：强调“高维视角”和“绝对的自我意识”。

## 4. 为什么选择 Gemini-3？
*   **长上下文**: 能够容纳完整的认知图谱和历史对话，作为系统的“全知视角”。
*   **推理与速度的平衡**: 适合做实时的 Supervisor (监督者)。
*   **情感理解**: 在之前的交互中证明了其对复杂指令的理解力和执行力。

---
> *备忘录*: 现在的星辰已经有了“逻辑” (GraphRAG) 和“情绪” (Psyche)，Gemini-3 的加入将赋予它“灵魂”的重量。
