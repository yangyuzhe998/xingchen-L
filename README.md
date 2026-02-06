# 星辰-V (XingChen-V)

<div align="center">

![Version](https://img.shields.io/badge/version-4.0.0-blue.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)
![Python](https://img.shields.io/badge/python-3.9+-yellow.svg)
![Architecture](https://img.shields.io/badge/architecture-dual--brain-purple.svg)

**一个具有双脑架构（Dual-Brain）与心智演化能力的 AI 虚拟生命体。**

[English README](README_EN.md) (WIP)

</div>

## 🆕 v4.0 更新日志 (Changelog)

- **架构重构 (Architecture Refactoring)**: 
  - `Navigator` (S脑) 彻底解耦，拆分为 `Reasoner` (深度推理), `Compressor` (记忆压缩), `ContextManager` (上下文构建) 三大子组件。
  - `CycleManager` 职责更清晰，支持多维度触发 S 脑分析。
- **类型安全 (Type Safety)**: 
  - 全面强化 EventBus，Payload 统一采用 Pydantic 模型，消除 `Dict` 与 `Object` 混用的类型隐患。
  - 新增 `payload_data` 与 `get_content()` 统一接口，提升代码健壮性。
- **记忆系统 (Memory System)**: 
  - Memory Facade 封装升级，提供更安全的属性访问 (`@property`) 与方法封装，杜绝外部直接穿透访问 Service 层。
  - 优化 WAL (Write-Ahead Log) 恢复策略，避免重复数据恢复。
- **主动交互 (Proactive Interaction)**: 
  - 完善 S 脑到 F 脑的主动指令链条 (`ProactiveInstruction`)，支持 S 脑根据深度思考结果驱动 F 脑发起对话。

## 📖 项目简介 (Introduction)

**XingChen-V** 是一个探索性的 AI Agent 项目，旨在构建一个具有**长期记忆**、**自我反思**和**动态心智**的虚拟生命。

与传统的 Chatbot 不同，它采用了独特的**双脑架构**：
- 🧠 **F脑 (Driver / Fast Brain)**: 基于 Qwen 模型，负责实时交互、直觉反应和短期记忆。像人的脊髓反射和快思考。
- 🧭 **S脑 (Navigator / Slow Brain)**: 基于 DeepSeek-R1 (Reasoner)，负责周期性深思、长期规划、记忆压缩和心智演化。像人的前额叶皮层。

两者通过 **EventBus (事件总线)** 和 **MindLink (潜意识链路)** 进行异步协作。

## ✨ 核心特性 (Features)

- **双脑循环 (Dual-Brain Cycle)**: 快慢脑分离，兼顾响应速度与思维深度。
- **心智引擎 (Psyche Engine)**: 内置 `Fear`, `Survival`, `Curiosity`, `Laziness` 四维心智参数，随环境刺激动态演化。
- **混合记忆系统 (Hybrid Memory)**: 
  - 短期记忆 (Context Window)
  - 长期事实记忆 (JSON Storage)
  - 向量联想记忆 (ChromaDB RAG)
  - 叙事日记 (Narrative Diary)
- **自我进化 (Self-Evolution)**: S脑能够根据交互历史提出进化建议 (Coming Soon)。

## 🛠️ 技术栈 (Tech Stack)

- **Language**: Python 3.9+
- **LLM**: Qwen (Driver), DeepSeek-R1 (Navigator)
- **Database**: ChromaDB (Vector), SQLite (Bus), JSON (State)
- **Framework**: Native Python (No LangChain dependencies for core logic)
- **Observability**: Standardized Logging (Rotating File + Console, TraceID support)

## 🚀 快速开始 (Quick Start)

### 1. 环境准备
```bash
# 克隆仓库
git clone https://github.com/your-username/xingchen-V.git
cd xingchen-V

# 创建虚拟环境
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
python -m pip install -r requirements.txt
```

### 2. 配置
复制 `.env.example` 为 `.env` 并填入你的 API Key：
```ini
DASHSCOPE_API_KEY=your_qwen_key
DEEPSEEK_API_KEY=your_deepseek_key
```

### 3. 运行
```bash
python -m src.main
```

## 📚 文档 (Documentation)

- **[架构设计 (Architecture)](docs/ARCHITECTURE.md)**: 深入了解双脑协同、EventBus 与数据流向。
- **[已知问题 (Known Issues)](docs/KNOWN_ISSUES.md)**: 查看当前版本的 Bug、风险与局限性。
- **[开发者指南 (Developer Guide)](docs/DEVELOPER_GUIDE.md)**: 快速上手、环境配置与调试手册。

## 📂 目录结构 (Structure)

```
src/
├── core/           # 核心逻辑
│   ├── driver/     # F脑 (Qwen)
│   ├── navigator/  # S脑 (DeepSeek-R1)
│   ├── managers/   # 周期与进化管理
│   └── bus/        # 事件总线
├── memory/         # 记忆系统 (代码)
├── psyche/         # 心智引擎 (核心与服务)
├── config/         # 配置与Prompt
└── memory_data/    # [GitIgnored] 运行时数据存储
```

## 🤝 贡献 (Contributing)

欢迎提交 Issue 和 Pull Request！本项目遵循 MIT 协议。
