# 记忆模块 (Memory Module) 技术文档

## 1. 概述 (Overview)

记忆模块是星辰-V (XingChen-V) 的核心组件之一，负责管理数字生命的所有记忆数据。它不仅仅是一个简单的数据库封装，而是一个包含**多模态存储**、**数据安全保障**、**自动化维护**的复杂子系统。

记忆模块的设计目标是实现：
*   **持久性 (Persistence)**：确保记忆在系统重启或崩溃后不丢失。
*   **一致性 (Consistency)**：通过 WAL 和原子写入保证数据完整性。
*   **多维性 (Multi-dimensionality)**：同时支持非结构化文本、向量嵌入、结构化图谱等多种数据形态。

---

## 2. 架构设计 (Architecture)

记忆模块采用 **Facade 模式**，通过 `src.memory.memory_core.Memory` 类作为对外统一入口，内部协调多个子服务和存储引擎。

### 2.1 核心组件

1.  **Memory Core (`src.memory.memory_core.Memory`)**
    *   **角色**：门面 (Facade)。
    *   **职责**：对外暴露 `add_short_term`, `add_long_term`, `search` 等高层接口；管理 WAL (Write-Ahead Log) 的生命周期。
    
2.  **Memory Service (`src.memory.services.memory_service.MemoryService`)**
    *   **角色**：业务逻辑层 (Service Layer)。
    *   **职责**：处理具体的 CRUD 逻辑，协调不同的存储引擎（如同时写入 JSON 和 Vector DB）。管理数据的 Dirty Flags (脏标记)。

3.  **Storage Engines (存储引擎)**
    *   **Vector Storage (`ChromaStorage`)**: 基于 ChromaDB，用于语义检索 (RAG)。
    *   **Local Storage (`JsonStorage`)**: 基于 JSON 文件，用于存储可读的长期记忆列表。
    *   **Graph Storage (`GraphMemory`)**: 基于 NetworkX，用于存储实体关系图谱 (GraphRAG)。
    *   **Diary Storage (`DiaryStorage`)**: 专门用于存储日记流。
    *   **WAL (`WriteAheadLog`)**: 预写日志，用于灾难恢复。

---

## 3. 关键机制 (Key Mechanisms)

### 3.1 数据安全与 WAL (Write-Ahead Log)
为了防止系统在写入过程中崩溃导致数据丢失，我们引入了数据库级别的 WAL 机制。

*   **写入流程**：
    1.  调用 `Memory.add_short_term`。
    2.  **先写日志**：将操作指令追加到 `memory_data/wal.log`。
    3.  **再执行内存操作**：更新内存中的列表或对象。
    4.  **最后异步持久化**：在 checkpoint (如 `force_save_all`) 时将内存数据刷入磁盘。
    5.  **清空日志**：数据落盘成功后，清空 WAL。

*   **崩溃恢复**：
    *   系统启动时，`Memory._replay_wal()` 会检查 WAL 文件。
    *   如果发现未清空的日志，说明上次非正常退出。
    *   系统会自动重放日志中的操作，将数据恢复到崩溃前的状态。

### 3.2 智能保存 (Smart Save & Dirty Check)
为了减少磁盘 I/O，我们实现了**脏标记 (Dirty Flag)** 机制。

*   **机制**：
    *   `MemoryService` 和各 Storage 类内部维护 `_dirty` 标记。
    *   当数据发生变化（如 `append`）时，`_dirty` 设为 `True`。
    *   调用 `save()` 时，检查 `_dirty`。如果是 `False`，直接跳过文件写入。

### 3.3 原子写入 (Atomic Write)
在 `JsonStorage` 中，为了防止文件在写入一半时断电导致文件损坏（变成全 0 或截断），我们使用了**原子替换**策略。

*   **实现**：
    1.  先将数据写入临时文件 `filename.tmp`。
    2.  调用 `os.replace(temp, target)` 将临时文件重命名为目标文件。
    3.  操作系统保证 `replace` 操作是原子的：要么成功，要么失败，不会出现“半个文件”的情况。

---

## 4. 数据结构 (Data Structures)

### 4.1 目录结构
所有记忆数据默认存储在 `e:\xingchen-V\src\memory_data\`：

| 文件/目录 | 说明 | 格式 |
| :--- | :--- | :--- |
| `chroma_db/` | 向量数据库文件 | SQLite + Bin |
| `storage.json` | 长期记忆列表 | JSON |
| `short_term_cache.json` | 短期记忆缓存 (未归档) | JSON |
| `wal.log` | 预写日志 | JSON Lines |
| `archive.db` | 归档数据库 (Diary) | SQLite |
| `bus.db` | 事件总线历史 | SQLite |

### 4.2 记忆条目模型

*   **ShortTermMemoryEntry**:
    ```python
    {
        "role": "user" | "assistant" | "system",
        "content": "...",
        "timestamp": "ISO-8601",
        "metadata": {}
    }
    ```
*   **LongTermMemoryEntry**:
    ```python
    {
        "content": "...",
        "category": "fact" | "rule" | "experience",
        "created_at": "ISO-8601",
        "metadata": {}
    }
    ```

---

## 5. 实现细节与代码索引

*   **入口 Facade**: [`src.memory.memory_core.Memory`](../src/memory/memory_core.py)
*   **业务逻辑**: [`src.memory.services.memory_service.MemoryService`](../src/memory/services/memory_service.py)
*   **WAL 实现**: [`src.memory.storage.write_ahead_log.WriteAheadLog`](../src/memory/storage/write_ahead_log.py)
*   **向量存储**: [`src.memory.storage.vector.ChromaStorage`](../src/memory/storage/vector.py)
*   **图谱存储**: [`src.memory.storage.graph.GraphMemory`](../src/memory/storage/graph.py)

---

## 6. 层级记忆扩展 (Hierarchical Memory Extension) 🆕

> 新增于 v2.0-自主学习版 (2026-02-07)

### 6.1 知识库 (Knowledge Database)

基于 SQLite 的结构化知识存储，支持精确查询。

*   **文件**: [`src.memory.storage.knowledge_db.KnowledgeDB`](../src/memory/storage/knowledge_db.py)
*   **数据库**: `memory_data/knowledge.db`

**表结构**:

| 表名 | 用途 |
|------|------|
| `knowledge` | 存储验证过的事实 (content, category, source, confidence) |
| `entities` | 存储实体及别名 (name, aliases, entity_type) |

**使用示例**:
```python
from src.memory.storage.knowledge_db import knowledge_db

# 添加知识
knowledge_db.add_knowledge("DeepSeek R1于2025年发布", category="fact", source="s_brain")

# 搜索知识
results = knowledge_db.search_knowledge("DeepSeek")

# 实体别名解析
knowledge_db.add_entity("User", aliases=["老杨", "仔仔"])
knowledge_db.resolve_alias("仔仔")  # → "User"
```

### 6.2 话题管理器 (Topic Manager)

基于 ChromaDB 的层级记忆结构：Topic → Task → Fragment。

*   **文件**: [`src.memory.storage.topic_manager.TopicManager`](../src/memory/storage/topic_manager.py)
*   **数据库**: `memory_data/topic_db/`

**层级结构**:
```
Topic (话题，如"Python学习")
  └── Task (任务，如"异步编程")
        └── Fragment (片段，具体记忆内容)
```

**使用示例**:
```python
from src.memory.storage.topic_manager import topic_manager

# 创建层级
topic_id = topic_manager.create_topic("技术学习")
task_id = topic_manager.create_task(topic_id, "Python进阶")

# 添加片段
topic_manager.add_fragment("async/await用法", topic_id=topic_id, task_id=task_id)

# 按话题搜索
results = topic_manager.search_fragments("异步", topic_id=topic_id)
```

### 6.3 自动分类器 (Auto Classifier)

使用 S脑 (DeepSeek) 自动将对话归类到话题。

*   **文件**: [`src.memory.services.auto_classifier.AutoClassifier`](../src/memory/services/auto_classifier.py)

**使用示例**:
```python
from src.memory.services.auto_classifier import auto_classifier

# 分类并存储
fragment_id = auto_classifier.classify_and_store("用户想学习Python异步编程")
```

---

## 7. 时间工具 (Time Utilities) 🆕

*   **文件**: [`src.utils.time_utils`](../src/utils/time_utils.py)

**功能**:
- `parse_relative_time("昨天")` → datetime
- `format_time_ago(datetime)` → "2小时前"
- `get_time_context()` → 生成时间上下文字符串

---

> 文档生成时间: 2026-02-07
> 生成者: XingChen-V (Self-Reflection)

