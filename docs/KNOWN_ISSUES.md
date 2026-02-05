# 已知问题与风险记录 (Known Issues & Risks)

> 文档版本: v1.0.0
> 最后更新: 2026-02-05

本文档记录了 XingChen-V 当前版本存在的已知技术问题、架构局限性以及潜在的风险点。

## 1. 交互体验问题 (UX Issues)

### 1.1 主动对话重复 (Proactive Repetition)
*   **现象**: S-Brain 有时会忘记刚才已经生成过类似的“主动开口指令”，导致 F-Brain 在短时间内重复发起相似的话题。
*   **状态**: **已修复 (v0.2.1)**。
    *   引入了 `PROACTIVE_COOLDOWN` (60s)。
    *   在 Prompt 中增加了“禁止重复”的强约束。
    *   **注意**: 仍需长期观察，极端情况下（如 S-Brain 幻觉）仍可能发生。

### 1.2 称呼反复 (Addressing Instability)
*   **现象**: AI 在“亲密度”规则和“用户偏好”之间摇摆，有时会突然改口叫“先生”，下一句又叫“老杨”。
*   **状态**: **已修复 (v0.2.1)**。
    *   修改了 Prompt 优先级，明确 `用户偏好 > 亲密度`。
    *   **建议**: 未来应建立专门的 `UserProfile` 模块持久化存储称呼偏好。

### 1.3 伪即时性 (Pseudo-Realtime)
*   **现象**: 用户说完话后，记忆并不是立即写入的。如果在 S-Brain 归档前（约 5 分钟窗口期）系统崩溃或重启，这 5 分钟的对话会丢失。
*   **原因**: 依赖异步的 `CycleManager` 进行记忆压缩。
*   **风险**: 数据一致性风险。

## 2. 架构局限性 (Architectural Limitations)

### 2.1 单体进程瓶颈 (Monolithic Process)
*   **描述**: 目前所有的模块（Driver, Navigator, Web Server, Vector DB Client）都运行在同一个 Python 进程中。
*   **影响**:
    *   如果 S-Brain 进行大规模计算（如全量记忆整理），可能会阻塞主线程（尽管用了 Threading，但在 Python GIL 下仍有影响）。
    *   无法利用多核 CPU 优势。
*   **未来方案**: 需要拆分为微服务架构（Driver Service, Navigator Service, Memory Service）。

### 2.2 记忆熵增 (Memory Entropy)
*   **描述**: 随着运行时间增长，数据库（特别是 Vector DB 和 Graph）会不断膨胀。
*   **风险**: 检索准确率下降，响应变慢，出现“幻觉记忆”。
*   **缺失**: 目前缺乏高效的“遗忘机制” (Forgetting Mechanism)。`DeepClean` 功能尚处于实验阶段。

## 3. 安全与部署风险 (Security & Deployment Risks)

### 3.1 认知污染 (Cognitive Pollution)
*   **描述**: 如果接入互联网，S-Brain 可能会抓取并内化错误信息或有害价值观。
*   **现状**: **无防护**。目前缺乏独立的“价值过滤层” (Value Alignment Layer)。
*   **建议**: 在本地测试阶段，严禁赋予 AI 社交网络账号或不受限的写权限。

### 3.2 资源消耗 (Resource Consumption)
*   **描述**: 24 小时运行模式下，如果逻辑死循环，可能导致 Token 消耗失控。
*   **现状**: **无熔断**。目前缺乏 Token 消耗速率限制。
*   **建议**: 上线前必须实现 `RateLimiter` 和 `BudgetManager`。

### 3.3 权限过大 (Over-Privileged)
*   **描述**: AI 运行在用户主机上，拥有文件系统的读写权限。
*   **风险**: 误删文件或修改系统配置。
*   **建议**: 生产环境必须运行在 Docker 容器或受限的虚拟机中。

---

**接手建议**:
在解决上述“安全与部署风险”之前，**严禁**将本项目部署到公网服务器或赋予其无人值守的互联网访问权限。
