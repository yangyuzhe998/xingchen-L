# XingChen-V 全面重构计划

将 `src/` 下的全部代码迁移至新的 `xingchen/` 包，同时修复缺陷、消除硬编码、升级项目管理。**旧 `src/` 保留不动**，确认无误后再删除。

## User Review Required

> [!IMPORTANT]
> 1. 新包名使用 `xingchen/`，旧 `src/` 保持不动，两者并存直到确认可删
> 2. 运行数据目录 ([memory_data/](file:///d:/xingchen-V/tests/conftest.py#12-22)) 将移到项目根目录 [data/](file:///d:/xingchen-V/src/schemas/events.py#70-81)，旧数据文件需手动迁移或重新开始
> 3. [requirements.txt](file:///d:/xingchen-V/requirements.txt) 将迁移至 `pyproject.toml`
> 4. 情绪关键词列表、漂移因子等将从硬编码改为配置文件 (`xingchen/config/emotion_rules.yaml`)，可热编辑

## Proposed Changes

### 1. 项目结构与依赖管理

#### [NEW] [pyproject.toml](file:///d:/xingchen-V/pyproject.toml)
- 替代 [requirements.txt](file:///d:/xingchen-V/requirements.txt)，使用 PEP 621 标准声明项目元数据和依赖
- 补齐遗漏依赖：`fastapi`, `uvicorn[standard]`, `jinja2`, `sse-starlette`
- 声明 `[project.scripts]` 入口点：`xingchen = "xingchen.main:main"`

#### [NEW] 新目录结构
```
xingchen/               # 主包（替代 src/）
├── __init__.py
├── main.py             # 入口 (CLI / Web)
├── app.py              # [NEW] Application Factory — 依赖注入
├── config/
│   ├── __init__.py
│   ├── settings.py     # 扁平化配置（去掉 settings/settings.py 嵌套）
│   ├── prompts.py      # Prompt 模板
│   └── emotion_rules.yaml  # [NEW] 情绪规则配置（外化硬编码）
├── core/
│   ├── __init__.py
│   ├── driver.py       # F脑（从 driver/engine.py 扁平化）
│   ├── navigator.py    # S脑（从 navigator/core.py 扁平化）
│   ├── event_bus.py    # 事件总线（从 bus/ 扁平化）
│   └── cycle/          # 周期管理（保留子包）
│       ├── __init__.py
│       ├── manager.py
│       └── triggers/
├── psyche/
│   ├── __init__.py     # [重写] 通用 LazyProxy + 干净导出
│   ├── engine.py       # 心智引擎
│   ├── values.py       # 价值观系统
│   ├── mind_link.py    # 潜意识通道
│   └── emotion.py      # [NEW] 情绪检测器（从 Driver 抽离）
├── memory/
│   ├── __init__.py
│   ├── facade.py       # [瘦身] 精简 Facade，WAL 逻辑移出
│   ├── wal.py          # [NEW] WAL 独立模块
│   ├── service.py      # 记忆服务（原 memory_service.py）
│   ├── models.py       # 数据模型（从 models/entry.py 扁平化）
│   ├── storage/        # 存储后端
│   │   ├── __init__.py
│   │   ├── vector.py
│   │   ├── local.py
│   │   ├── diary.py
│   │   ├── graph.py
│   │   └── knowledge_db.py
│   └── services/
│       ├── auto_classifier.py
│       └── orchestrator.py
├── tools/
│   ├── __init__.py
│   ├── registry.py     # 工具注册（去掉 Proxy）
│   ├── definitions.py
│   ├── loader.py
│   └── builtin/
│       ├── system_tools.py
│       └── web_tools.py
├── managers/           # 管理器（从 core/managers 提升）
│   ├── __init__.py
│   ├── evolution.py
│   ├── library.py
│   ├── sandbox.py
│   └── shell.py
├── schemas/
│   ├── __init__.py
│   └── events.py       # 事件模型（统一 Enum，无魔法字符串）
├── ui/
│   ├── __init__.py
│   ├── web/            # [拆分] Web UI
│   │   ├── __init__.py
│   │   ├── app.py      # FastAPI app creation
│   │   ├── routes.py   # HTTP 路由
│   │   ├── sse.py      # SSE 事件处理
│   │   └── templates/
│   └── cli.py          # CLI 调试界面
├── utils/
│   ├── __init__.py
│   ├── llm_client.py
│   ├── logger.py
│   ├── json_parser.py
│   ├── time_utils.py
│   └── proxy.py        # [NEW] 通用 LazyProxy 工厂
└── interfaces/
    └── ui_interface.py
```

---

### 2. 硬编码外化

#### [NEW] [emotion_rules.yaml](file:///d:/xingchen-V/xingchen/config/emotion_rules.yaml)
将以下散布在代码中的硬编码值集中到 YAML 配置文件：

| 原位置 | 硬编码内容 | 迁移目标 |
|--------|-----------|---------|
| `driver.py` L404-413 | `positive_words` / `negative_words` 列表 | `emotion_rules.yaml → user_sentiment.positive / negative` |
| `driver.py` L399-413 | 情绪 delta 数值 (0.2, 0.3, 0.1) | `emotion_rules.yaml → emotion_deltas` |
| [cycle/manager.py](file:///d:/xingchen-V/src/core/managers/cycle/manager.py) L256 | 漂移因子 `persistence = 0.02` | `settings.py → BASELINE_DRIFT_PERSISTENCE` |
| [cycle/manager.py](file:///d:/xingchen-V/src/core/managers/cycle/manager.py) L259-263 | 情绪→维度映射 | `emotion_rules.yaml → baseline_drift_mapping` |
| [cycle/manager.py](file:///d:/xingchen-V/src/core/managers/cycle/manager.py) L268 | 漂移阈值 `avg > 0.2` | `settings.py → BASELINE_DRIFT_THRESHOLD` |
| [memory_service.py](file:///d:/xingchen-V/src/memory/services/memory_service.py) L199 | 触景生情系数 `0.1` | `settings.py → EMOTIONAL_RESONANCE_FACTOR` |
| [llm_client.py](file:///d:/xingchen-V/src/utils/llm_client.py) L38 | `glm-4` | `settings.py → ZHIPU_DEFAULT_MODEL` |
| [llm_client.py](file:///d:/xingchen-V/src/utils/llm_client.py) L42 | `qwen-turbo` | `settings.py → QWEN_DEFAULT_MODEL` |
| [system_tools.py](file:///d:/xingchen-V/src/tools/builtin/system_tools.py) L81-85 | `DANGEROUS_COMMANDS` 列表 | `settings.py → SHELL_DANGEROUS_COMMANDS` |
| [system_tools.py](file:///d:/xingchen-V/src/tools/builtin/system_tools.py) L109 | Shell 类型 `"powershell"` | `settings.py → SHELL_EXECUTABLE` (支持 bash/cmd) |
| [system_tools.py](file:///d:/xingchen-V/src/tools/builtin/system_tools.py) L117 | 输出截断 `1000` 字符 | `settings.py → SHELL_OUTPUT_MAX_CHARS` |
| [mind_link.py](file:///d:/xingchen-V/src/psyche/services/mind_link.py) L25-26 | 衰减/过期秒数 `3600/7200` | `settings.py → INTUITION_WEAKEN_SECONDS / EXPIRE_SECONDS` |
| `driver.py` L87 | 轮询礼仪后缀 [("?", "？", "呢", "吗")](file:///d:/xingchen-V/src/core/driver/engine.py#466-469) | `emotion_rules.yaml → question_suffixes` |
| `driver.py` L319 | LLM 工具循环次数 `3` | `settings.py → MAX_TOOL_CALL_ROUNDS` |
| `driver.py` L312 | 上下文历史窗口 `15` | `settings.py → CONTEXT_HISTORY_WINDOW` |

#### [MODIFY] [settings.py](file:///d:/xingchen-V/xingchen/config/settings.py)
- 增加上表中的新配置项
- 清理已废弃的 Moltbook 配置
- 数据目录改为 [data/](file:///d:/xingchen-V/src/schemas/events.py#70-81)（从 `src/memory_data/`）
- 按模块分组加注释

---

### 3. 缺陷修复

#### Thread Safety — PsycheEngine
- `apply_emotion()` 和 `update_state()` 加 `threading.Lock`
- 避免 F脑和 S脑并发修改 `self.state`

#### Dead Code — EvolutionManager
- `process_request()` 在行 58 `return` 后有 ~50 行永远不会执行的代码
- 清理并保留为注释文档说明设计意图

#### Event Type 混乱
- `web_app.py` L270 硬编码字符串 `"psyche_update"`、`"psyche_delta"` 
- 补充到 `EventType` 枚举，全局统一使用 Enum 值

#### TemplateResponse 兼容性
- 已在部署时修复，迁移时保持正确的 Starlette 1.0.0 API

#### LLMClient 配置不一致
- `_configure()` 中 `zhipu` 和 `qwen` provider 的默认模型硬编码在代码里
- 统一由 `settings` 提供，`_configure()` 只读取

---

### 4. 架构改善

#### [NEW] 通用 LazyProxy — [proxy.py](file:///d:/xingchen-V/xingchen/utils/proxy.py)
```python
def lazy_proxy(factory_fn, base_class):
    """一行创建延迟初始化代理，替代 5 套重复的 Proxy 样板"""
```
替代 `psyche/__init__.py` (80 行)、`event_bus.py` (20 行)、`registry.py` (12 行) 中的重复代码。

#### [NEW] Application Factory — [app.py](file:///d:/xingchen-V/xingchen/app.py)
- 集中管理组件初始化和依赖注入
- 替代 `main.py` 中 `create_app()` / `start_cli()` 的重复初始化代码

#### [NEW] EmotionDetector — [emotion.py](file:///d:/xingchen-V/xingchen/psyche/emotion.py)
- 将 Driver `_finalize_interaction` 中的情绪检测逻辑抽到独立模块
- 读取 `emotion_rules.yaml` 中的关键词和 delta 配置
- 暴露 `detect_user_sentiment(text) → Dict[str, float]` 接口

#### Web UI 拆分
- `web_app.py` (352行) → `routes.py` (HTTP 路由) + `sse.py` (EventBus 事件推送) + `app.py` (FastAPI 初始化)

---

### 5. 迁移顺序

按依赖层次从底到顶，确保每步都能独立运行：

```
1. utils/ (无外部依赖)
2. config/ (依赖 utils)
3. schemas/ (依赖 pydantic)
4. memory/storage/ (依赖 config)
5. memory/ (依赖 storage + config)
6. psyche/ (依赖 config + event_bus)
7. core/event_bus (依赖 config + schemas)
8. tools/ (依赖 config)
9. managers/ (依赖 tools + memory + psyche)
10. core/driver + navigator (依赖 managers + psyche + memory)
11. ui/ (依赖 core + psyche)
12. main.py + app.py (顶层组装)
```

---

## Verification Plan

### Automated Tests
已有 14 个测试文件，迁移后需要更新 import 路径：

```bash
# 运行全部测试
py -m pytest tests/ -v

# 单独运行关键模块测试
py -m pytest tests/test_core/test_psyche.py -v
py -m pytest tests/test_core/test_event_bus.py -v
py -m pytest tests/test_memory/ -v
py -m pytest tests/test_utils/ -v
```

### 启动验证
```bash
# Web 模式启动
py -m xingchen.main web
# 验证首页: curl http://127.0.0.1:8000
# 验证 API: curl http://127.0.0.1:8000/api/status?key=<your_key>
```

### Manual Verification
1. 启动 Web 服务器后，在浏览器访问 `http://127.0.0.1:8000?key=<your_key>`
2. 发送一条消息，确认 F脑回复正常
3. 在侧边栏查看心智状态是否实时更新
4. 检查 `data/` 目录下的文件是否正确生成（psyche_state.json、short_term_cache.json 等）
