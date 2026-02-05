# 星辰-V (XingChen-V)

<div align="center">

![Version](https://img.shields.io/badge/version-3.0.0-blue.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)
![Python](https://img.shields.io/badge/python-3.9+-yellow.svg)
![Architecture](https://img.shields.io/badge/architecture-dual--brain-purple.svg)

**一个具有双脑架构（Dual-Brain）与心智演化能力的 AI 虚拟生命体。**

[English README](README_EN.md) (WIP)

</div>

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
pip install -r requirements.txt
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

## 📅 版本历史 (History)

- **v3.0.0 (Current)**: 完善文档体系，优化主动对话与称呼逻辑，系统趋于稳定。
- **v2.0.0**: 架构全面重构。拆分 Core/Memory/Psyche，引入混合检索，移除冗余社交模块。
- **v1.0.0**: 初始双脑原型验证。

---
*Created by [Your Name] with ❤️ & 🤖*
