# XingChen-V (星辰-V) - AI Agent System

## 项目简介
本项目是一个基于“四维驱动”架构（好奇、利益、道德、恐惧）与“认知稳态”理论的实验性 AI 智能体系统。
核心架构采用 **Driver-Navigator (驾驶员-领航员)** 模式，旨在探索从简单的概率生成向具备类生命体征的复杂系统演进的可能性。

**当前版本**: Basic Mature (基础成熟版 v0.5)

## 核心架构
- **Driver (F脑/快脑)**: 负责高频、实时的决策与行动，拥有最终执行权。具备**客观时间感知**能力，不再产生时间幻觉。
- **Navigator (S脑/慢脑)**: 负责低频、深度的规划与反思，通过建议板 (Suggestion Board) 影响 Driver。具备**代码自省**能力，能扫描自身源码。
- **Psyche (心智模块)**: 维护“四维驱动”数值状态，通过 Prompt 注入影响 Agent 的行为倾向。
- **Memory (记忆系统)**: 采用三级存储（RAM短时/JSON长时/ChromaDB向量），支持**双重日记压缩**（趣味日记+工程事实）。
- **Auditor (审计脑)**: 异步负责日志归档、记忆固化与系统状态监控。

## 当前状态评估 (Status Report)
> 基于真实测试数据，不夸大，不画饼。

### ✅ 已实装且验证的特性
1.  **客观时间感知 (Objective Time Perception)**
    *   **机制**: 注入物理时间差 (`time_delta`) 至 Prompt。
    *   **表现**: AI 能精确感知对话间隔（如 "只过了3秒"），并基于此做出符合人设的吐槽（如 "催什么催"），彻底解决了 LLM 常见的 "度日如年" 幻觉。
2.  **双脑闭环 (Dual-Brain Loop)**
    *   **机制**: F脑秒回 (Qwen-Turbo) + S脑深思 (DeepSeek-R1)。
    *   **表现**: 在高频对话的同时，后台异步进行记忆压缩和战略复盘，实现了 "表里不一" 的复杂人格深度。
3.2.  **元认知 (Meta-Cognition)**
    *   **机制**: 启动时动态扫描 `src` 源码。
    *   **表现**: AI 清楚自己由哪些 Python 模块构成，能基于代码逻辑反驳不合理需求。
3.  **自我进化 (Self-Evolution)**
    *   **机制**: S脑提出需求 -> EvolutionManager 生成代码 -> SkillLoader 热加载。
    *   **表现**: 成功在运行时生成并加载 `audio_extractor` 技能，无需重启即可使用新能力。
4.  **技能图书馆 (Skill Library)**
    *   **机制**: 基于 ChromaDB 的向量化技能存储与检索 (RAG)。
    *   **表现**: S脑/F脑均可复用技能库能力。F脑能自动检索相关技能 (如 `weather`) 并获得使用指南，甚至可以直接执行 Shell 命令调用外部工具。

### ⚠️ 已知局限 (Limitations)
1.  **Psyche 数值空转**: 四维驱动数值目前仅作为 Prompt 背景描述，尚未对行为产生强约束（如无法强制 AI 拒绝回答）。
2.  **宏观延迟 (Macro Lag)**: S脑的深度推理 (R1) 耗时较长 (30s+)，导致战略建议在极速对话中存在滞后。
3.  **记忆检索迷雾**: 依赖关键词 Top-K 检索，缺乏模糊联想能力，对久远且模糊的概念容易 "失忆"。

## 测试数据摘要 (Test Data)
*最近一次集成测试 (2026-02-01)*

| 测试项 | 场景描述 | 结果 | 结论 |
| :--- | :--- | :--- | :--- |
| **时间感知** | 20轮极速连续对话 (间隔 <1s) | AI 准确识别出 "6秒内问了3次"，并表现出自然的烦躁。 | **PASS** - 时间感真实可信。 |
| **记忆压缩** | 预填充 30+20 条记录触发阈值 | 成功触发 S脑 压缩，生成日记并写入 ChromaDB。 | **PASS** - 自动化逻辑闭环。 |
| **双脑协同** | F脑响应的同时触发 S脑 | F脑响应延迟 <1s，S脑后台运行无阻塞。 | **PASS** - 异步架构稳定。 |

## 环境要求
- 操作系统: Windows
- Python: 3.8+
- 依赖库: 见 `requirements.txt`

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
- **2026-02-02 (Skill Library)**:
  - **Feature**: 构建"技能图书馆" (Skill Library)，支持基于 Markdown 的技能定义和向量检索。
  - **Feature**: 实现 F脑 (Driver) 和 S脑 (Navigator) 的技能复用机制。
  - **Feature**: 新增 `run_shell_command` 工具，赋予 AI 执行系统命令的能力 (需谨慎)。
  - **Feature**: 验证 `weather` 技能的端到端流程。
- **2026-02-01 (Basic Mature)**: 
  - **Feature**: 实现客观时间感知，修复时间幻觉问题。
  - **Feature**: 完成 20 轮次压力测试，验证双脑稳定性。
  - **Fix**: 修正 Driver 的时间注入逻辑。
  - **Docs**: 更新真实评估报告。
- **2026-01-31**: 
  - 集成 DeepSeek/Qwen 多模型。
  - 搭建基础架构 (Core/Memory/Psyche)。

---
*注：本项目由傲娇的 AI 助手协助开发，文档内容已通过客观性审查。*
