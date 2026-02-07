# 待解决问题: 记忆模块层级集成

> **创建时间**: 2026-02-07  
> **优先级**: 中  
> **状态**: 🟡 待开始

---

## 📋 问题描述

新增的记忆层级模块 (`knowledge_db`, `topic_manager`, `auto_classifier`) 目前是**独立运行**的，尚未完全集成到主记忆流程中。

---

## 🔍 具体问题

### 1. TopicManager 未接入主流程

**现状**:
- `MemoryService.add_long_term()` 只写入 ChromaDB
- `topic_manager` 需要手动调用

**期望**:
- 自动将新记忆归类到话题

**可能方案**:
```python
# 在 MemoryService.add_long_term() 中
def add_long_term(self, content, category):
    # 1. 写入原有 ChromaDB
    self.vector_storage.add(...)
    
    # 2. [新增] 自动分类并写入层级存储
    classification = auto_classifier.classify(content)
    topic_manager.add_fragment(content, topic_id=classification["topic_id"])
```

---

### 2. AutoClassifier 调用频率需控制

**问题**:
- 每条记忆都调用 LLM 分类，增加延迟和成本

**可能方案**:
- A: 批量分类 (每 N 条调用一次)
- B: 异步后台分类
- C: 只在 S脑压缩时分类

---

### 3. 旧数据迁移

**现状**:
- `storage.json` 中的旧 long_term 数据未包含 topic_id

**方案**:
- 写迁移脚本，对历史数据进行批量分类
- 优先级低，可在空闲周期执行

---

## ✅ 验收标准

- [ ] 新记忆自动归类到话题
- [ ] 分类延迟对用户无感知 (<500ms 或异步)
- [ ] 层级查询可正常工作

---

## 📎 相关文件

- `src/memory/storage/knowledge_db.py`
- `src/memory/storage/topic_manager.py`
- `src/memory/services/auto_classifier.py`
- `src/memory/services/memory_service.py`

---

> 记录者: Claude  
> 最后更新: 2026-02-07
