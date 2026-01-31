# 核心模块详解 (Core Modules)

## 1. Driver (F脑)

`src/core/driver.py`

Driver 是系统的实时交互接口，类似于人类的“快思考”系统。

### 核心逻辑 (Logic)

1.  **接收输入**: 监听用户消息。
2.  **构建上下文**:
    *   获取最近对话历史 (ShortTerm Memory)。
    *   检索相关长期记忆 (LongTerm Memory)。
    *   读取当前心智状态 (PsycheState)。
    *   读取 S脑建议 (Suggestion)。
3.  **生成回复**: 调用 Qwen/GLM 模型生成回复，同时输出 `inner_voice` (内心独白) 和 `emotion` (情绪识别)。
4.  **发布事件**: 将交互结果发布到 EventBus。

### 关键方法

*   `think(user_input, psyche_state, suggestion)`: 核心思考循环。
*   `act(action)`: 执行具体工具调用。

---

## 2. Navigator (S脑)

`src/core/navigator.py`

Navigator 是系统的深度思考引擎，类似于人类的“慢思考”系统。

### 核心逻辑 (Logic)

1.  **Prefix Caching (前缀缓存)**:
    *   `_build_static_context()`: 动态扫描 `src/` 下所有 Python 文件，构建静态代码库上下文。这部分内容在多次请求间保持不变，利用 DeepSeek 缓存机制降低成本。
2.  **周期性分析 (Cycle Analysis)**:
    *   `analyze_cycle()`: 从 EventBus 获取最近 N 条事件。
    *   结合代码上下文和交互历史，进行 R1 深度推理。
3.  **输出决策**:
    *   **Suggestion**: 给 Driver 的自然语言建议。
    *   **Delta**: 四维心智状态的修正值。
    *   **Memory**: 需要固化的长期记忆事实。

---

## 3. EventBus (事件总线)

`src/core/bus.py`

基于 SQLite 的持久化消息队列。

### 特性

*   **Thread-Safe**: 使用 `threading.Lock` 保证写入安全。
*   **Indexing**: 对 timestamp 和 type 建索引，加速查询。
*   **JSON Serialization**: 自动处理 payload 和 meta 的序列化/反序列化。
