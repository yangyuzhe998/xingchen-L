# 记忆模块 (Memory Module) 文档

## 1. 简介
记忆模块是星辰-V 的存储中心，负责管理短期工作记忆、长期语义记忆以及情景日记。它保证了 AI 的连续性和人格的稳定性。

## 2. 目录结构
```
src/memory/
├── models/          # 数据模型 (Entry, Block)
├── services/        # 业务逻辑服务
├── storage/         # 存储后端实现
│   ├── vector.py    # 向量数据库 (ChromaDB)
│   ├── local.py     # 本地文件存储 (JSON)
│   └── diary.py     # Markdown 日记管理
├── memory_core.py   # 统一入口 (Facade)
└── __init__.py
```

## 3. 记忆分层

### 3.1 短期记忆 (Short-Term Memory)
- **介质**: RAM (Python List)。
- **容量**: 滑动窗口 (默认 50 条消息或 20k tokens)。
- **作用**: 提供 LLM 对话的直接上下文。
- **机制**: 当超出容量时，触发 **Memory Archival** 流程，将旧消息压缩并存入长期记忆。

### 3.2 长期记忆 (Long-Term Memory)
- **介质**: ChromaDB (Vector) + JSON (Structured)。
- **类型**:
  - **Fact (事实)**: 纯粹的信息点（如“用户喜欢 Python”）。存入 ChromaDB。
  - **Episode (情景)**: 关键事件的摘要。存入 ChromaDB 和 Diary。
- **检索**: 支持语义检索 (Similarity Search) 和关键词过滤。

### 3.3 日记系统 (Diary)
- **介质**: `src/memory_data/diary.md`
- **格式**: Markdown。
- **风格**: 以第一人称（星辰）撰写，带有强烈的情感色彩。
- **作用**:
  - 人格锚点：AI 通过重读日记来找回“感觉”。
  - 可读性：用户可以直接阅读，了解 AI 的内心世界。

## 4. 关键流程

### 4.1 记忆归档 (Archival)
1. 短期记忆缓冲区满。
2. 调用 S-Brain 进行总结。
3. S-Brain 生成：
   - **Diary Entry**: 写入 `diary.md`。
   - **Knowledge Points**: 向量化存入 ChromaDB。
4. 清空缓冲区，仅保留最近 N 条。

### 4.2 记忆检索 (Retrieval)
1. F-Brain 接收用户输入。
2. 提取输入中的关键词和语义向量。
3. 在 ChromaDB 中检索 Top-K 相关条目。
4. 将检索结果注入到 System Prompt 的 `long_term_context` 区域。
