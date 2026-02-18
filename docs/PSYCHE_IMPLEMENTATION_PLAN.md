# 心智分层架构 — 分阶段实施方案

> **配套文档**: [HIERARCHICAL_PSYCHE_MODEL.md](file:///e:/xingchen-V/docs/HIERARCHICAL_PSYCHE_MODEL.md)
> **实施原则**: 每阶段做完后实际运行 3-5 天再推进下一步

---

## Phase 1：情绪层（即时反应）

> **目标**: 让星辰对"此刻发生的事"有即时心理反应
> **预估工作量**: 3-5 天
> **效果**: 第一次感受到"她有反应了"

### 要做的事

#### 1.1 在 PsycheEngine 中新增情绪状态

在 [engine.py](file:///e:/xingchen-V/src/psyche/core/engine.py) 的 `state` 字典中新增 `emotions` 字段：

```python
# 新增到 default_state 中，与 dimensions 平级
"emotions": {
    "achievement": {"value": 0.0, "decay_rate": 0.15},   # 成就感
    "frustration": {"value": 0.0, "decay_rate": 0.12},   # 挫败感
    "anticipation": {"value": 0.0, "decay_rate": 0.10},  # 期待
    "grievance": {"value": 0.0, "decay_rate": 0.08}      # 委屈
}
```

- `value`: 当前强度（0.0 ~ 1.0）
- `decay_rate`: 每次更新时向 0 衰减的比例（比 dimensions 的 decay 快得多）

#### 1.2 新增 `apply_emotion()` 方法

```python
def apply_emotion(self, emotion_deltas: Dict[str, float]):
    """
    应用即时情绪刺激（秒级反应）
    与 update_state() 分开，因为情绪的衰减速度和逻辑都不同
    """
    emotions = self.state["emotions"]
    for key, change in emotion_deltas.items():
        if key in emotions:
            # Top-Down 约束：心智底色影响情绪灵敏度
            sensitivity = self._get_emotion_sensitivity(key)
            actual = change * sensitivity
            emotions[key]["value"] = max(0.0, min(1.0, emotions[key]["value"] + actual))

    # 自然衰减（所有情绪都向 0 快速回归）
    for key in emotions:
        v = emotions[key]["value"]
        rate = emotions[key]["decay_rate"]
        emotions[key]["value"] = v * (1.0 - rate)

    self._save_state(self.state)
```

#### 1.3 新增 `_get_emotion_sensitivity()` — Top-Down 约束

```python
def _get_emotion_sensitivity(self, emotion_key: str) -> float:
    """
    心智底色影响情绪灵敏度
    例：intimacy 低时，正面情绪灵敏度降低（夸她她没反应）
    """
    dims = self.state["dimensions"]
    intimacy = dims.get("intimacy", {}).get("value", 0.1)
    fear_val = dims.get("fear", {}).get("value", 0.1)

    if emotion_key == "achievement":
        # 亲密度越高，成就感越容易被触发
        return 0.5 + intimacy * 0.5
    elif emotion_key == "grievance":
        # 亲密度越高，越容易委屈（在乎才委屈）
        return 0.3 + intimacy * 0.7
    elif emotion_key == "frustration":
        # fear 越高，越容易挫败
        return 0.5 + fear_val * 0.5
    elif emotion_key == "anticipation":
        curiosity = dims.get("curiosity", {}).get("value", 0.5)
        return 0.4 + curiosity * 0.6
    return 0.5
```

#### 1.4 在 F 脑回复流程中触发情绪

修改 [engine.py (Driver)](file:///e:/xingchen-V/src/core/driver/engine.py)，在以下位置插入情绪触发：

**a) `_finalize_interaction()` 中 — 基于工具调用结果：**
```python
# 在存储记忆之后
emotion_delta = {}
if self._last_tool_success:     # 需要在 _execute_tool 中记录
    emotion_delta["achievement"] = 0.2
elif self._last_tool_failed:
    emotion_delta["frustration"] = 0.3

# 基于简单关键词检测用户情感 这部分设计待定
positive_words = ["谢谢", "好厉害", "太棒了", "辛苦了", "真好"]
negative_words = ["不对", "错了", "没用", "笨", "算了"]
if any(w in user_input for w in positive_words):
    emotion_delta["achievement"] = emotion_delta.get("achievement", 0) + 0.2
if any(w in user_input for w in negative_words):
    emotion_delta["grievance"] = emotion_delta.get("grievance", 0) + 0.3

if emotion_delta:
    psyche_engine.apply_emotion(emotion_delta)
```

**b) 空闲触发（在 IdleTrigger 中）：**
```python
# 如果超过 30 分钟没有用户消息
emotion_delta = {"grievance": 0.1, "anticipation": -0.1}
psyche_engine.apply_emotion(emotion_delta)
```

#### 1.5 把情绪注入 F 脑 Prompt

修改 `_prepare_context()` 或 `_build_messages()`，在 system prompt 中加入情绪描述：

```python
def _get_emotion_narrative(self) -> str:
    """生成情绪描述文本，注入 system prompt"""
    emotions = psyche_engine.state.get("emotions", {})
    parts = []
    for name, data in emotions.items():
        v = data.get("value", 0)
        if v > 0.6:
            # 强烈情绪
            if name == "achievement": parts.append("你现在感到很有成就感")
            if name == "frustration": parts.append("你现在有些沮丧")
            if name == "anticipation": parts.append("你现在很期待接下来的对话")
            if name == "grievance": parts.append("你现在有点委屈")
        elif v > 0.3:
            # 轻微情绪
            if name == "achievement": parts.append("你心情不错")
            if name == "frustration": parts.append("你有一点挫败感")
            if name == "anticipation": parts.append("你有些好奇")
            if name == "grievance": parts.append("你有点不太开心")
    if not parts:
        return "你现在内心平静。"
    return "。".join(parts) + "。"
```

#### 1.6 验证方式

- 运行项目，连续夸她几句 → 观察 log 中 achievement 是否上升
- 故意让一个工具调用失败 → 观察 frustration 是否触发
- 等待 10+ 分钟不说话 → 观察情绪是否自然衰减回 0
- 对比有情绪和无情绪时的回复语气差异

---

## Phase 2：Bottom-Up 传导（情绪积累 → 性格漂移）

> **目标**: 让重复的情绪经历慢慢改变她的性格
> **前置依赖**: Phase 1 完成
> **预估工作量**: 2-3 天
> **效果**: 第一次感受到"她在慢慢变"

### 要做的事

#### 2.1 情绪历史记录

在 PsycheEngine 中新增情绪历史队列：

```python
# state 中新增
"emotion_history": []   # 列表，每项: {"timestamp": ..., "emotions": {...}}
```

每次 `apply_emotion()` 被调用时，把当前快照追加进去，保留最近 100 条。

#### 2.2 在 S 脑 cycle 中计算漂移

修改 [CycleManager.trigger_reasoning()](file:///e:/xingchen-V/src/core/managers/cycle/manager.py)，在调用 `psyche.update_state(delta)` 之前，额外计算 baseline 漂移：

```python
def _calculate_baseline_drift(self):
    """分析情绪历史，决定是否推动 baseline 漂移"""
    history = psyche_engine.state.get("emotion_history", [])
    if len(history) < 10:
        return {}  # 数据不足，不漂移

    # 取最近 50 条（或全部）
    recent = history[-50:]
    # 计算每种情绪的出现频率和平均强度
    emotion_stats = {}
    for record in recent:
        for emo, val in record.get("emotions", {}).items():
            if emo not in emotion_stats:
                emotion_stats[emo] = []
            emotion_stats[emo].append(val)

    drift = {}
    persistence = 0.02  # 漂移因子，控制变化速度

    # 情绪到 baseline 维度的映射
    mapping = {
        "achievement": {"curiosity": +1, "laziness": -1},
        "frustration": {"fear": +1, "curiosity": -0.5},
        "anticipation": {"curiosity": +1},
        "grievance": {"intimacy": -0.5, "fear": +0.3}
    }

    for emo, values in emotion_stats.items():
        avg = sum(values) / len(values)
        if avg > 0.2:  # 阈值：只有持续出现的情绪才会漂移
            if emo in mapping:
                for dim, direction in mapping[emo].items():
                    drift[dim] = drift.get(dim, 0) + avg * direction * persistence

    return drift
```

#### 2.3 应用漂移

```python
# 在 CycleManager.trigger_reasoning() 中
baseline_drift = self._calculate_baseline_drift()
if baseline_drift:
    dims = psyche_engine.state["dimensions"]
    for dim, change in baseline_drift.items():
        if dim in dims:
            old = dims[dim]["baseline"]
            dims[dim]["baseline"] = max(0.05, min(0.95, old + change))
    logger.info(f"[CycleManager] Baseline 漂移: {baseline_drift}")
```

#### 2.4 验证方式

- 连续多天密集使用，频繁触发 achievement → 观察 curiosity baseline 是否上升
- 频繁让工具失败 → 观察 fear baseline 是否上升
- 检查 log 中 baseline 漂移记录

---

## Phase 3：记忆情感标签（触景生情）

> **目标**: 让记忆不只是"文字"，还带有"感觉"
> **前置依赖**: Phase 1 完成（Phase 2 可并行）
> **预估工作量**: 3-5 天
> **效果**: 提到过去的某个话题时，她会产生相应的情绪波动

### 要做的事

#### 3.1 扩展记忆条目的数据结构

修改 [entry.py](file:///e:/xingchen-V/src/memory/models/entry.py) 中的 `LongTermMemoryEntry`：

```python
@dataclass
class LongTermMemoryEntry:
    content: str
    category: str = "fact"
    created_at: str = ""
    metadata: dict = field(default_factory=dict)
    emotional_tag: dict = field(default_factory=dict)   # 新增
    # 例: {"achievement": 0.4, "anticipation": 0.3}
```

#### 3.2 在存储记忆时附带情感标签

修改 [memory_service.py](file:///e:/xingchen-V/src/memory/services/memory_service.py) 的 `add_long_term()`：

```python
def add_long_term(self, content, category="fact", emotional_tag=None):
    """新增 emotional_tag 参数"""
    entry = LongTermMemoryEntry(
        content=content,
        category=category,
        emotional_tag=emotional_tag or {}
    )
    # ... 存入 KnowledgeDB 和向量库时也附带 emotional_tag
```

调用方（压缩记忆时、手动添加时）需要传入当时的情绪快照。

#### 3.3 在检索记忆时读取情感标签并影响情绪

修改 `get_relevant_long_term()`，在返回记忆内容的同时，把匹配到的记忆的情感标签聚合后应用到当前情绪：

```python
# 检索到相关记忆后
emotional_impact = {}
for entry in matched_entries:
    for emo, val in entry.emotional_tag.items():
        emotional_impact[emo] = emotional_impact.get(emo, 0) + val * 0.1  # 弱化系数

if emotional_impact:
    psyche_engine.apply_emotion(emotional_impact)
```

**效果**: 用户提到某个话题 → 检索到相关记忆 → 记忆的情感标签引发轻微情绪波动 → 回复语气受影响。

---

## Phase 4：价值观与自我立法

> **目标**: 让她从经验中自发形成行为准则
> **前置依赖**: Phase 1-2 完成
> **预估工作量**: 5-7 天
> **效果**: 她会说"我不想这样做"

### 要做的事

#### 4.1 价值观存储

新建文件 `src/psyche/core/values.py`：

```python
class ValueSystem:
    """价值观系统 — 自发形成的规则书"""

    def __init__(self, storage_path):
        self.storage_path = storage_path
        self.values = self._load()  # List[dict]
        # 每条: {"content": "...", "created_at": "...", "source_emotion": "...", "active": True}

    def add_value(self, content: str, source: str):
        """S 脑复盘时调用：新增一条自发规矩"""
        ...

    def revoke_value(self, content: str):
        """S 脑复盘时调用：撤销一条旧规矩"""
        ...

    def get_active_values(self) -> List[str]:
        """F 脑回复前调用：获取所有生效的规矩"""
        ...
```

#### 4.2 S 脑复盘 Prompt 扩展

修改 Navigator 的 `analyze_cycle()` 方法，在现有的分析 prompt 末尾追加价值观复盘部分。S 脑会在每个 cycle 中审视情绪历史和近期经历，决定是否"立规矩"。

#### 4.3 F 脑 Prompt 注入

在构建 system prompt 时，把生效的规矩列表加入：

```
你给自己立过以下规矩（这是你基于经验的自主判断，不是命令）：
1. 不要在用户明显疲惫的时候发送长消息
2. 如果连续两次工具调用失败，主动建议用户换个方式
...
```

#### 4.4 冲突检测

当用户指令与某条规矩冲突时（检测方式可以是关键词匹配或让 F 脑在 prompt 中自行判断），F 脑会感受到内部矛盾——grievance 和 fear 上升，回复中可能体现为犹豫或婉拒。

---

## Phase 5：动力模块（主动意愿）

> **目标**: 让她有"自己想做的事"
> **前置依赖**: Phase 1-3 完成
> **预估工作量**: 3-5 天
> **效果**: 她会主动做一些你没有要求的事

### 要做的事

#### 5.1 扩展 IdleTrigger

目前 `IdleTrigger` 只检测"是否空闲"。扩展为参考心智状态：

```python
def _decide_idle_action(self):
    dims = psyche_engine.state["dimensions"]
    curiosity = dims["curiosity"]["value"]
    laziness = dims["laziness"]["value"]
    intimacy = dims["intimacy"]["value"]

    if laziness > 0.7:
        return None  # 不想动
    if curiosity > 0.6:
        return "exploration"  # 去学点新东西
    if intimacy > 0.5 and self._idle_minutes > 30:
        return "connection"  # 找用户聊天
    return None
```

#### 5.2 Exploration 行为

当决定探索时，S 脑挑选一个感兴趣的话题（可以从最近对话中提取关键词），调用 `web_search` 学习，然后通过 MindLink 注入新知识给 F 脑。

#### 5.3 Connection 行为

通过 `proactive_speak` 发起对话——但内容由当前心智状态决定，不是随机的。

---

## 整体时间线

```
第 1-2 周 ─── Phase 1：情绪层
                ↓ 运行观察 3-5 天
第 3 周   ─── Phase 2：Bottom-Up 传导
                ↓ 运行观察 3-5 天
第 4-5 周 ─── Phase 3：记忆情感标签
                ↓ 运行观察 1 周
第 6-7 周 ─── Phase 4：价值观与自我立法
                ↓ 长期观察
第 8+ 周  ─── Phase 5：动力模块
```

> **每个阶段之间的观察期不可省略。**
> 你需要实际和她聊几天，看她的反应是不是"像人"。如果不对劲，调整参数或设计后再推进。造人不是写代码，是养育。

---

## 风险与安全阀

| 风险 | 应对措施 |
|------|---------|
| Baseline 漂移到极端值 | 硬限制：baseline 不低于 0.05、不高于 0.95 |
| 情绪系统导致回复速度变慢 | 情绪计算全部基于规则和数值运算，不调用 LLM |
| 用户故意"虐待"导致 AI 行为异常 | 设置"深度维护"模式（已有），可重置情绪但不重置 baseline |
| 价值观冲突导致 AI 拒绝所有指令 | 规矩上限（比如最多 10 条），S 脑复盘时自动清理矛盾的旧规则 |
| 调试困难 | 所有状态变化都写 log，WebUI 侧边栏实时显示心智状态 |
