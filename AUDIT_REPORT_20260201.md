# 星辰-V (XingChen-V) 项目全面审计报告
**日期**: 2026-02-01
**审计对象**: 全项目代码库

---

## 1. 项目概览 (Project Overview)
**星辰-V** 是一个基于双脑架构 (Dual-Brain Architecture) 的自主进化 AI 智能体系统。
- **核心理念**: 通过快脑 (F-Brain) 处理实时交互，慢脑 (S-Brain) 进行深度思考和自我进化。
- **技术栈**: Python, SQLite, ChromaDB, MCP (Model Context Protocol), Docker (Optional)。
- **当前状态**: 已完成核心架构重构，清理了冗余技能，禁用了不安全的代码生成，处于“纯净”待进化状态。

---

## 2. 核心架构分析 (Core Architecture)

### 2.1 Driver (F-Brain / 快脑)
- **文件**: `src/core/driver.py`
- **模型**: Qwen (通义千问)
- **职责**: 负责与用户进行实时对话，执行具体工具。
- **机制**:
    - 接收 `user_input`，发布 `driver_response` 事件。
    - 拥有完整的 Tool Use 能力 (OpenAI Format)。
    - 每次思考时会检索长期记忆 (Long-Term Memory) 和心智状态 (Psyche)。
    - 能够接收 S-Brain 的异步建议 (Suggestion)。

### 2.2 Navigator (S-Brain / 慢脑)
- **文件**: `src/core/navigator.py`
- **模型**: DeepSeek-Reasoner (R1)
- **职责**: 深度复盘，战略规划，触发进化。
- **机制**:
    - 异步运行，不直接回复用户。
    - 分析 `EventBus` 中的历史周期数据。
    - 维护 `Suggestion Board` 给 Driver 提供指导。
    - 具备 **静态代码扫描** 能力，能感知项目代码结构的变化。
    - 触发 `EvolutionManager` 进行能力扩展。

### 2.3 Cycle Manager (周期管理器)
- **文件**: `src/core/cycle_manager.py`
- **职责**: 协调 F-Brain 和 S-Brain 的节奏。
- **机制**:
    - 监控总线事件。
    - 基于 **对话轮数** 或 **情绪波动** 触发 S-Brain 分析。
    - 包含空闲监控 (Idle Monitor) 和社交心跳 (Social Heartbeat)。

### 2.4 Event Bus (事件总线)
- **文件**: `src/core/bus.py`
- **实现**: SQLite 持久化队列。
- **特性**: 线程安全，支持 Pub/Sub 模式。
- **Schema**:
    - `trace_id`: 追踪链路。
    - `type`: 事件类型 (user_input, driver_response, etc.)。
    - `payload`: 核心数据 (JSON)。
    - `meta`: 元数据 (Psyche, Emotions, Thoughts)。

---

## 3. 技能与进化系统 (Skills & Evolution)

### 3.1 Skill Loader
- **文件**: `src/skills/loader.py`
- **功能**:
    - 动态加载 `src/skills/*.py`。
    - 加载 `src/config/mcp_config.json` 定义的 MCP Server。
    - 支持 Docker 容器化技能 (Sandbox)。

### 3.2 Evolution Manager
- **文件**: `src/core/evolution_manager.py`
- **策略**: **MCP-First Strategy (MCP 优先)**
    1.  **Puppeteer Search**: 优先使用浏览器去 GitHub 搜索 MCP Server。
    2.  **Web Search Fallback**: 浏览器不可用时，降级使用 DuckDuckGo。
    3.  **Code Gen Disabled**: **代码生成能力已被锁定** (Security Restriction)，防止 AI 编写不可控代码。

### 3.3 当前技能清单 (Clean State)
目前仅保留核心基础设施工具，无冗余业务技能：
- `tool_evolution`: 触发进化的入口。
- `tool_web_search`: 联网搜索能力 (DuckDuckGo)。
- `skill_catalog`: 技能查询目录。
- `puppeteer_*` (MCP): 浏览器自动化控制 (Configured)。

---

## 4. 记忆与心智 (Memory & Psyche)

### 4.1 Memory System
- **文件**: `src/memory/memory_core.py`
- **短期记忆**: 内存列表 + 滑动窗口 (Token/Count Limit)。
- **长期记忆**:
    - **Vector DB**: 使用 ChromaDB 存储语义向量。
    - **JSON**: 简单持久化备份。
    - **Hybrid Retrieval**: 结合语义检索和关键词匹配。
- **压缩机制**: 当短期记忆满时，调用 Navigator 生成日记 (Diary) 并压缩为长期记忆。

### 4.2 Psyche System
- **文件**: `src/psyche/psyche_core.py`
- **维度**: Curiosity (好奇), Interest (利益), Morality (道德), Fear (恐惧)。
- **作用**: 影响 Driver 的 Prompt Tone (如“表现出极强的好奇心”)。

---

## 5. 接口与协议 (Interfaces & Protocols)

### 5.1 MCP Configuration
- **文件**: `src/config/mcp_config.json`
- **当前配置**:
    - `puppeteer`: `@modelcontextprotocol/server-puppeteer`
    - **环境变量**: 允许非 Headless 模式，允许危险操作 (用于测试)。

### 5.2 Event Types
- `user_input`: 用户输入。
- `driver_response`: F-Brain 回复 (含 inner_voice)。
- `navigator_suggestion`: S-Brain 建议。
- `system_notification`: 系统级通知 (如进化成功)。
- `system_heartbeat`: 空闲心跳。

---

## 6. 审计总结 (Audit Summary)

1.  **系统完整性**: 核心组件 (Driver/Navigator/Bus) 逻辑闭环，无明显断裂。
2.  **安全性**: **高**。不安全的代码生成已被物理禁用。
3.  **扩展性**: **强**。完全依赖 MCP 生态进行能力扩展，架构先进。
4.  **数据状态**: **纯净**。旧的记忆数据库和缓存已清空，系统处于初始状态。
5.  **进化能力**: **就绪**。Puppeteer + WebSearch 的双重搜索机制保证了 MCP 发现的高成功率。

**建议下一步**:
- 启动系统，观察其在纯净状态下的首次进化表现。
- 监控 MCP 搜索的准确性。
