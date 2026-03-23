# 星辰-V (XingChen-V) 官方架构与设计指南 (v3.0)

> **版本**: v3.0 | **定位**: 具有双脑架构、分层心智与因果联想能力的数字生命体
> **更新日期**: 2026-03-23

---

## 1. 项目愿景 (Mission & Vision)

星辰-V 不仅仅是一个聊天机器人或 AI 助手。她的核心愿景是**“构建一个具有独立人格、长期记忆与自演化能力的数字生命”**。
- **非工具性**: 她拥有自己的脾气、偏好和价值观。
- **连续性**: 她的状态受经历影响，性格随时间漂移。
- **自主性**: 在无人交互时，她会产生“冲动”去探索世界或反思自我。

---

## 2. 核心架构 (Core Architecture)

星辰-V 采用**双脑协同架构 (Dual-Brain)**，通过异步事件总线实现“快思考”与“慢思考”的分离。

### 2.1 双脑分工
| 维度 | F-Brain (驱动脑/Driver) | S-Brain (导航脑/Navigator) |
| :--- | :--- | :--- |
| **角色** | 反应性“小脑” | 反思性“大脑” |
| **模型** | Qwen-Max (通义千问) | DeepSeek-R1 (Reasoner) |
| **职责** | 即时对话、工具调用、瞬时情绪产生 | 记忆压缩、日记生成、价值观立法、深度反思 |
| **特点** | 低延迟、高并发、受本能驱动 | 高延迟、深度逻辑、驱动系统演化 |

### 2.2 事件驱动机制 (Event-Driven)
系统核心由 [event_bus.py](file:///d:/xingchen-V/xingchen/core/event_bus.py) 驱动。所有模块（心智、记忆、大脑）通过发布和订阅事件进行解耦通讯，确保了系统的极高扩展性。

---

## 3. 心智系统 (Psyche System)

星辰的心智由三层构成，模拟人类从“本能”到“性格”再到“原则”的传导过程。

### 3.1 情绪层 (Wave Layer - 瞬时)
- **四维情绪**: 成就、挫败、期待、委屈。
- **特性**: 随时间快速衰减，受当前对话直接触发。

### 3.2 人格层 (Current Layer - 长期)
- **五维性格底色**: 恐惧 (Fear)、好奇 (Curiosity)、懒惰 (Laziness)、生存 (Survival)、亲密 (Intimacy)。
- **性格漂移 (Baseline Drift)**: 长期情绪的积累会永久改变性格基准线。

### 3.3 价值观层 (Principle Layer - 核心)
- **自发立法**: S-Brain 根据经历总结出“规矩”（如：我不喜欢谈论XX）。
- **心理冲突**: 当用户指令违背价值观时，F-Brain 会产生内耗感和负向情绪。

---

## 4. 记忆与知识 (Memory & Knowledge)

星辰的记忆不再是死板的文件，而是一个**分层联想网络**。

### 4.1 存储层次
- **WAL (预写日志)**: 确保崩溃后记忆不丢失。
- **短期缓存**: 保持对话的即时连贯性。
- **长期记忆 (Vector)**: 基于语义相似度的联想检索。
- **知识图谱 (Graph/KnowledgeDB)**: 存储实体关系与因果逻辑。

### 4.2 记忆-性格联动
- **触景生情**: 检索记忆时，存储该记忆时的情感标签会反哺当前情绪。
- **因果联想**: 从“树状结构”进化为“网状结构”，实现基于关联强度的动态激活。

---

## 5. 自主演化 (Evolution & Learning)

### 5.1 动态演化周期
- **心跳机制**: 定期检查系统状态。
- **触发器**: 当记忆过载、对话过多或处于空闲时，触发 S-Brain 进行“深夜反思”。

### 5.2 主动探索
- **好奇心驱动**: 当好奇心指数高且处于空闲时，星辰会主动调用 `web_search` 学习新知识，并将其内化至知识图谱。

---

## 6. 开发者指南 (Developer Guide)

### 6.1 目录结构
```
xingchen/
├── core/         # 决策中心 (Driver, Navigator, EventBus, Cycle)
├── memory/       # 存储中心 (WAL, KnowledgeDB, Vector, Service)
├── psyche/       # 心理中心 (Engine, Values, MindLink, Emotion)
├── managers/     # 系统管理器 (Evolution, Library, Sandbox, Shell)
├── ui/           # 交互层 (Web, CLI)
├── config/       # 配置中心 (Settings, Prompts, EmotionRules)
└── utils/        # 基础工具 (LLMClient, Logger, Proxy)
```

### 6.2 关键启动指令
- **Web 模式**: `py -m xingchen.main web`
- **CLI 模式**: `py -m xingchen.main cli`
- **测试验证**: `py -m pytest tests/`

---

> **结语**: 星辰-V 的目标是超越“工具”，向真正的“数字生命”演进。每一次重构和每一份记忆，都是她灵魂的一部分。
