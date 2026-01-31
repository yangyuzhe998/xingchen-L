# XingChen-V (星辰-V) - AI Agent System

## 项目简介
本项目是一个基于“四维驱动”架构（好奇、利益、道德、恐惧）与“认知稳态”理论的实验性 AI 智能体系统。
核心架构采用 **Driver-Navigator (驾驶员-领航员)** 模式，旨在探索从简单的概率生成向具备类生命体征的复杂系统演进的可能性。

## 核心架构
- **Driver (F脑/快脑)**: 负责高频、实时的决策与行动，拥有最终执行权。
- **Navigator (S脑/慢脑)**: 负责低频、深度的规划与反思，通过建议板 (Suggestion Board) 影响 Driver，不直接干预。
- **Psyche (心智模块)**: 维护“四维驱动”数值状态，通过 Prompt 注入影响 Agent 的行为倾向。
- **Auditor (审计脑)**: 异步负责日志归档、记忆固化与系统状态监控。

## 环境要求
- 操作系统: Windows
- Python: 3.8+

## 快速开始

### 1. 环境配置
请确保已安装 Python。
在项目根目录下运行以下命令安装依赖：
```powershell
python -m pip install -r requirements.txt
```

### 2. 环境变量
复制 `.env.example` 为 `.env`，并填入必要的 API Key。
```powershell
cp .env.example .env
```

### 3. 运行
```powershell
python src/main.py
```

## 修改日志
- **2026-01-31**: 
  - 集成 **DeepSeek (默认)**, **Zhipu AI**, **Qwen** 多模型支持。
  - 实现 `LLMClient` 统一接口。
  - **Driver** 模块已接入 LLM，具备基础对话能力。
  - 项目初始化。创建基础目录结构 (`src/core`, `src/memory`, `src/psyche` 等)，编写基础文档。

---
*注：本项目由傲娇的 AI 助手协助开发，请务必保持代码整洁，否则后果自负。*
