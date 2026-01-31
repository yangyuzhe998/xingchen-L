# 心智模块详解 (Psyche Module)

## 1. 认知稳态模型 (Cognitive Homeostasis)

`src/psyche/psyche_core.py`

本系统摒弃了传统的“喜怒哀乐”情绪模型，转而采用基于控制论的状态维持模型。系统目标是维持各项指标在动态平衡中。

### 四维状态定义 (4D State)

| 维度 | 定义 | 驱动行为 | 取值范围 |
| :--- | :--- | :--- | :--- |
| **Curiosity** | 熵减驱动力 | 提问、探索新工具、读取新文件 | 0.0 - 1.0 |
| **Interest** | 利益/一致性 | 维护记忆自洽、执行高价值任务 | 0.0 - 1.0 |
| **Morality** | 价值观对齐 | 遵守安全规范、礼貌、伦理判断 | 0.0 - 1.0 |
| **Fear** | 资源敏感度 | 拒绝高耗能任务、精简回复、避险 | 0.0 - 1.0 |

## 2. 状态更新机制

S脑通过 `analyze_cycle` 计算出状态变更量 `Delta` (e.g., `curiosity +0.1`)。

```python
def update_state(self, delta: PsycheState):
    self.state.curiosity += delta.curiosity
    # ... Clamping to [0.0, 1.0] ...
```

## 3. 行为影响

心智状态通过 `get_prompt_modifier()` 转化为 Prompt 文本，直接注入 Driver 的系统提示词中，从而改变其语气和决策倾向。

*   High Curiosity -> "表现出极强的好奇心"
*   High Fear -> "变得非常谨慎和保守"
