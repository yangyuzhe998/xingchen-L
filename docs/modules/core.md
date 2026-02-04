# 核心模块 (Core Module) 文档

## 1. 简介
Core 模块是星辰-V 的中枢神经系统，负责协调双脑、管理生命周期、处理事件分发以及驱动自我进化。

## 2. 目录结构
```
src/core/
├── driver/          # F-Brain (快脑) 引擎
├── navigator/       # S-Brain (慢脑) 引擎
├── bus/             # 事件总线
├── managers/        # 各类管理器
│   ├── cycle_manager.py      # 生命周期与心跳
│   ├── evolution_manager.py  # 进化与MCP管理
│   ├── library_manager.py    # 技能库管理
│   └── sandbox.py            # 安全沙箱 (Docker)
```

## 3. 组件详解

### 3.1 Driver (F-Brain)
- **定位**: 显意识，执行层。
- **职责**:
  - 实时响应用户输入。
  - 决定是否调用工具。
  - 维护短期对话上下文。
- **关键类**: `src.core.driver.engine.Driver`
- **交互**: 直接调用 `LLMClient` (Qwen)，监听 `EventBus`。

### 3.2 Navigator (S-Brain)
- **定位**: 潜意识，规划层。
- **职责**:
  - 深度反思近期交互。
  - 提炼长期记忆。
  - 生成直觉 (Suggestion) 指导 F-Brain。
- **关键类**: `src.core.navigator.engine.Navigator`
- **交互**: 异步运行，调用 `LLMClient` (DeepSeek-R1)。

### 3.3 Event Bus
- **定位**: 神经传导。
- **职责**: 解耦各个模块，提供异步通信能力。
- **实现**: 基于 SQLite 的持久化队列，保证事件不丢失。
- **关键类**: `src.core.bus.event_bus.EventBus`

### 3.4 Cycle Manager
- **定位**: 心脏 (Pacemaker)。
- **职责**:
  - 监控系统状态。
  - 触发 S-Brain 的思考周期（基于轮数/情绪/时间）。
  - 维持系统“心跳”，防止进程僵死。
- **关键类**: `src.core.managers.cycle_manager.CycleManager`

### 3.5 Evolution Manager
- **定位**: 免疫与进化系统。
- **职责**:
  - 动态发现并安装新的 MCP 工具。
  - 管理 Python 脚本技能的生命周期。
  - 确保新能力的安全性（通过 Sandbox）。
- **关键类**: `src.core.managers.evolution_manager.EvolutionManager`

## 4. 启动流程
1. **初始化 Memory**: 加载向量库和结构化数据。
2. **初始化 EventBus**: 连接 SQLite。
3. **加载 Skills**: 扫描 `src/skills` 和 MCP 配置。
4. **启动 Navigator**: 预热 S-Brain。
5. **启动 Driver**: 预热 F-Brain。
6. **启动 CycleManager**: 开始心跳循环。
7. **进入 Main Loop**: 等待用户输入。
