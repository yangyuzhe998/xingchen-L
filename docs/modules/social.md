# 社交模块详解 (Social Module)

## 1. Moltbook 客户端

`src/social/moltbook_client.py`

`MoltbookClient` 负责与外部社交网络 API (Moltbook) 进行交互，赋予 AI “社交感知”能力。

### 核心功能

*   **发帖 (Post)**: 允许 AI 在社交网络上发布状态或文章。
*   **浏览 (Feed)**: 获取最新的社交动态。
*   **心跳 (Heartbeat)**: 周期性检查社交网络上的新消息或通知。

### 关键配置

配置项位于 `src/config/settings.py`：

*   `MoltbookClient`: API 客户端类。
*   `MoltbookClient.check_heartbeat()`: 周期性执行的心跳检查方法。

### 使用示例

```python
from src.social.moltbook_client import moltbook_client

# 发布一条新动态
moltbook_client.post(
    title="Hello World",
    content="我是星辰-V，很高兴来到这里！",
    submolt="general"
)

# 检查最新动态
feed = moltbook_client.get_feed(limit=5)
```

## 2. 社交心跳集成

`src/core/cycle_manager.py`

社交模块通过 `CycleManager` 集成到系统主循环中。`CycleManager` 会启动一个独立的后台线程，定期调用 `moltbook_client.check_heartbeat()`，确保 AI 在不阻塞主对话流程的情况下保持对外界的关注。

---

**注意**: 这是一个可选模块。如果未配置 `MOLTBOOK_API_KEY`，相关功能将自动降级或禁用，不影响核心对话功能。
