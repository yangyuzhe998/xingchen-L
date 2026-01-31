# 记忆模块详解 (Memory Module)

## 1. 混合检索策略 (Hybrid Retrieval)

`src/memory/memory_core.py`

为了提高记忆召回的准确性，系统采用混合检索机制：

1.  **语义检索 (Semantic)**:
    *   利用 ChromaDB (Vector Database) 和 Embedding 模型。
    *   擅长捕捉意图相关性 (e.g., "上次的项目" <-> "Project Alpha")。
2.  **关键词匹配 (Keyword)**:
    *   基于精确词汇匹配。
    *   擅长捕捉专有名词和特定术语。
3.  **时效性补充 (Recency)**:
    *   总是包含最近写入的 N 条记忆，防止遗忘最新信息。

## 2. 短期记忆 (ShortTerm)

*   **存储**: RAM (List)。
*   **管理**: 滑动窗口 (Sliding Window)。
    *   **Max Count**: 最多 50 条。
    *   **Max Chars**: 最多 20,000 字符 (防止 Token 溢出)。
*   **用途**: 提供当前会话的直接上下文。

## 3. 长期记忆 (LongTerm)

*   **存储**: JSON 文件 (可读性) + ChromaDB (检索性)。
*   **写入**: 由 S脑 (Navigator) 在深度分析后决定写入。
*   **结构**:
    ```json
    {
      "content": "用户偏好使用 Python",
      "category": "fact",
      "created_at": "2024-01-01T12:00:00"
    }
    ```
