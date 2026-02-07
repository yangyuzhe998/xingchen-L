# 自主学习与进化机制 (Autonomous Learning & Evolution) - RFC (v2.1)

> **状态**: In Progress (开发中)
> **优先级**: P1 (进行中)
> **发起人**: User & Gemini-3-Pro
> **日期**: 2026-02-07 (Updated)

---

## 1. 核心理念 (Core Philosophy)

本机制旨在赋予星辰-V (XingChen-V) **主动探索** 和 **自我成长** 的能力。
我们不追求构建一个全知全能的百科全书，而是希望培养一个有**独立人格、有偏好、且能从经验中学习**的数字生命。

### 1.1 三大原则 (Three Pillars)
1.  **信任底座 (Trust the Foundation)**: 依赖 LLM (DeepSeek/Qwen) 本身的安全红线和逻辑能力来过滤虚假/有害信息，不重复造轮子。
2.  **拥抱偏好 (Personality Bias)**: 允许并鼓励 AI 基于自身心智 (Psyche) 产生兴趣偏好，形成独特的知识结构。
3.  **达尔文式记忆 (Darwinian Memory)**: 经验的留存遵循“优胜劣汰”原则，效率至上，无效经验自动遗忘。

---

## 2. 机制设计 (Mechanism Design)

### 2.1 触发与驱动 (Trigger & Driver)
*   **触发源**: 
    *   **S脑周期 (S-Brain Cycle)**: 在空闲周期 (Idle Mode) 主动发起。 (目前绑定在 Navigator 的压缩周期中)
    *   **外部刺激 (Entropy Injection)**: 用户交互、时事热点、或者随机的“灵光一闪” (Random Seed)。
*   **决策逻辑**:
    *   `Psyche` 模块根据当前 `emotion` (情绪) 和 `personality` (性格) 生成搜索关键词。
    *   *Example*: 心情 `curiosity` 高 -> 搜索 "最新的量子物理进展"; 心情 `laziness` 高 -> 搜索 "如何高效摸鱼"。

### 2.2 采集与感知 (Acquisition)
*   **工具**: `web_search` (DuckDuckGo) + `web_crawl` (Crawl4AI)。
*   **策略**: **礼貌爬取 (Polite Crawling)**。
    *   严格遵守 `robots.txt`。
    *   限制频率 (Rate Limiting)。
    *   **隐私清洗**: 在存入记忆前，自动剔除类似手机号、邮箱等敏感 PII 信息。

### 2.3 消化与内化 (Digestion & Internalization)
这是一个从 **Data -> Information -> Knowledge -> Experience** 的升维过程。

1.  **短期缓存 (Staging)**: 
    *   [已实现] 使用本地文件系统 (`storage/knowledge_staging`) 作为临时缓冲区。
    *   抓取的 Markdown 文件按时间戳和哈希命名，防止冲突。
2.  **反思 (Reflection)**: 
    *   [已实现] S脑组件 `KnowledgeIntegrator` 定期扫描 Staging 区。
    *   *验证*: 通过 LLM (DeepSeek) 进行逻辑校验和去重。
    *   *提炼*: 使用 `KNOWLEDGE_INTERNALIZATION_PROMPT` 提取结构化的 **知识 (Knowledge)** 和 **经验 (Experience)**。
3.  **经验固化 (Consolidation)**:
    *   将提炼后的准则存入 **向量记忆库 (Vector Memory)**。
    *   **归档**: 处理完毕的原始文件移动到 `storage/knowledge_archive`。

### 2.4 资源控制 (Resource Gating)
为了防止“学习”变成“DDoS 自己”，引入 **资源监视器 (ResourceMonitor)**。

*   **熔断条件**:
    *   CPU 使用率 > 20%
    *   内存占用 > 60%
    *   检测到用户键鼠操作 (User Activity Detected)
*   **动作**: 立即暂停/挂起爬虫任务，释放资源。

---

## 3. 风险与对策 (Risk Mitigation)

| 风险点 | 对策 |
| :--- | :--- |
| **垃圾信息** | 依赖 DeepSeek 的逻辑推理能力识别谬误；建立“可信源白名单” (GitHub, Wiki, Papers)。 |
| **信息茧房** | 引入随机熵增 (Entropy)；S脑定期发起“跨领域探索”请求。 |
| **隐私法律** | 强制开启 robots.txt 遵守模式；本地 PII 过滤层。 |
| **资源耗尽** | 严格的 ResourceMonitor 熔断机制。 |

---

## 4. 下一步行动 (Next Steps)

- [x] **Phase 2.5**: 实现 `web_search` 和 `web_crawl` 工具链 (Acquisition)。
- [x] **Phase 3.3 (Early)**: 搭建临时缓存区 (File System Staging) 和 `KnowledgeIntegrator`。
- [ ] **Phase 3.1**: 实现 `ResourceMonitor` 基础组件。
- [ ] **Phase 3.2**: 在 S脑 (Navigator) 中增加独立的 `LearningTrigger` (Idle Mode 状态机)。
