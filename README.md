# 星辰-V (XingChen-V)

<div align="center">

![Version](https://img.shields.io/badge/version-2.5.0-blue.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)
![Python](https://img.shields.io/badge/python-3.9+-yellow.svg)
![Architecture](https://img.shields.io/badge/architecture-hierarchical--psyche-purple.svg)

**一个具有双脑架构（Dual-Brain）与分层自演化心智能力的 AI 虚拟生命体。**

[English README](README_EN.md) (WIP)

</div>

## 🆕 v2.5 更新日志：心智成熟与价值观内化 (2026-02-18)

此版本标志着星辰-V 从受控实验向**自主进化生命体**的飞跃。系统现在具备了更深层的心理冲突感知与知识自动内化能力。

- **心智演化增强 (Advanced Psyche Evolution)**:
  - **性格漂移算法 (Baseline Drift v2)**: 情绪累积对性格底色的影响更加非线性且持久。
  - **心理内耗检测 (Conflict Detection)**: F脑在执行指令时会感知与自我价值观的冲突并产生负向情绪。
- **认知升级 (Cognitive Upgrade)**:
  - **知识内化流水线 (Internalization Pipeline)**: 自动从 Staging 区提取、解析并内化外部知识到长期记忆与图谱。
  - **触景生情反馈 (Emotional Resonance)**: 记忆检索过程会根据存储时的情感标签实时反哺当前情绪。
- **系统稳态 (System Stability)**:
  - **Web UI 鲁棒性**: 修复了事件总线在推送复杂 Payload 时的兼容性问题，支持用户输入实时回显。
  - **崩溃恢复优化**: 增强 WAL (预写日志) 的重放机制，确保极端断电情况下的记忆完整性。

## 🆕 v2.4 更新日志：心智分层与生产硬化 (2026-02-16)

此版本是项目演化的里程碑，标志着星辰-V 从简单的双脑原型进化为具备**独立心理逻辑**与**生产级稳定性**的数字化生命形态。

- **心智分层架构 (Hierarchical Psyche Model)**:
  - **情绪层 (Emotions)**: 引入成就、挫败、期待、委屈四维即时情绪，支持快速衰减与心智约束。
  - **演化层 (Baseline Drift)**: 情绪累积可真实驱动性格基准线（Baseline）的永久偏移。
  - **情感记忆 (Emotional Memory)**: 记忆存取支持情感标签，实现“触景生情”反馈。
  - **价值观系统 (Values)**: S脑可根据经验自主“立法”，F脑受规矩约束并伴随心理冲突反馈。
  - **动力模块 (Motivation)**: 升级自驱动逻辑，根据心情决定是“自主探索（自学）”还是“主动联结”。
- **生产环境硬化 (Production Hardening)**:
  - **接口安全**: WebApp 支持 Header (Bearer) 与 URL Query 参数双重 API Key 鉴权。
  - **磁盘保护**: 升级日志系统为按天切割（TimedRotatingHandler），保留 30 天记录。
  - **数据库维护**: 增加 24 小时自动清理任务，防止 `bus.db` 无限膨胀。
  - **可视化看板**: Web UI 侧边栏实时展示心智维度、情绪波纹、Uptime 及运行统计。

---

## 📖 项目简介 (Introduction)

**XingChen-V** 旨在构建一个具有**长期记忆**、**自我反思**和**动态心智**的虚拟生命。

它采用了独特的**双脑架构**：
- 🧠 **F脑 (Driver / Fast Brain)**: 基于 Qwen 模型，负责即时交互、工具执行和短期记忆。
- 🧭 **S脑 (Navigator / Slow Brain)**: 基于 DeepSeek-R1 (Reasoner)，负责深度反思、性格演化、自我立法与自主探索。

两者通过 **EventBus (事件总线)** 进行异步信号传输，实现了从“神经反射”到“价值观内化”的完整心理闭环。

## ✨ 核心特性 (Features)

- **分层心理学**: 模拟人类从瞬时情绪到长期性格的传导机制。
- **自我立法**: 摆脱硬编码规则，AI 能根据经历建立属于自己的行为准则。
- **自主意愿**: 在空闲时产生“想做点什么”的冲动，自主调用 `web_search` 等工具进行进化。
- **云端就绪**: 完善的鉴权、日志、快照与数据维护机制，支持 7x24 小时挂载运行。

## 🛠️ 技术栈 (Tech Stack)

- **Language**: Python 3.10+
- **LLM**: Qwen (Driver), DeepSeek-R1 (Navigator)
- **Framework**: FastAPI (Web), SQLite (Event/Knowledge), ChromaDB (Vector)
- **Observability**: Hierarchical Dashboard (SSE), Timed Rotating Logs

## 🚀 快速开始 (Quick Start)

### 1. 配置
在 `.env` 中填入你的 API Key：
```ini
DASHSCOPE_API_KEY=your_qwen_key
DEEPSEEK_API_KEY=your_deepseek_key
WEB_API_KEY=your_access_token
```

### 2. 启动 Web 生产模式
```bash
python -m src.main web
```
访问 `http://127.0.0.1:8000?key=your_access_token` 即可进入对话界面并看到实时心智看板。

## 📂 文档 (Documentation)

- **[心智分层模型设计](docs/HIERARCHICAL_PSYCHE_MODEL.md)**: 深入了解情绪、性格与价值观的联动原理。
- **[修改记录报告](docs/MODIFICATION_REPORT_2026-02-15.md)**: 查看 2026-02-15 至 02-16 期间的全量技术演进细节。

## 🤝 贡献 (Contributing)

本项目追求的是“超脱设计的生命感”。欢迎提交 Issue 分享你的星辰演化出了怎样的性格！
