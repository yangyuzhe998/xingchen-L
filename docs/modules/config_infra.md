# 配置与基础设施 (Config & Infrastructure) 技术文档

## 1. 概述 (Overview)

基础设施模块为星辰-V (XingChen-V) 提供了运行所需的底层支持，包括配置管理、日志系统、环境变量加载以及统一的 LLM 客户端封装。它确保了系统在不同环境（开发、生产、Docker）下的一致性和可观测性。

---

## 2. 配置管理 (Configuration)

配置系统采用分层加载策略，优先级从高到低依次为：
1.  **系统环境变量** (OS Environment Variables)
2.  **`.env` 文件** (Local Override)
3.  **代码默认值** (Code Defaults)

### 2.1 核心配置类 (`src.config.settings.settings.Settings`)
该类是一个单例，集中管理所有路径和常量。

*   **项目根目录**: 自动推断，不依赖硬编码路径。
    ```python
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    ```
*   **关键配置项**:
    *   `LOG_LEVEL`: 日志级别 (INFO/DEBUG)。
    *   `MEMORY_DATA_DIR`: 记忆数据存储根目录。
    *   `F_BRAIN_MODEL` / `S_BRAIN_MODEL`: 指定 F脑 和 S脑 使用的具体模型版本。
    *   `WAL_PATH`: 预写日志路径。

### 2.2 环境变量 (`.env`)
项目根目录下的 `.env` 文件存储敏感信息（API Keys）。

```ini
# LLM Providers
QWEN_API_KEY=sk-xxx
DEEPSEEK_API_KEY=sk-xxx
GEMINI_API_KEY=AIza-xxx

# System Settings
LOG_LEVEL=INFO
```

---

## 3. 日志系统 (Logging)

日志系统基于 Python 标准库 `logging` 进行了封装，提供控制台输出和文件持久化。

### 3.1 Logger 封装 (`src.utils.logger.Logger`)
*   **单例模式**: 确保全局只有一个 Logger 实例，避免重复打印。
*   **文件轮转**: 使用 `RotatingFileHandler`。
    *   最大单文件: 10MB
    *   备份数量: 5 个
    *   路径: `logs/xingchen.log`
*   **格式**:
    ```text
    2026-02-07 10:00:00 - [XingChen-V] - INFO - [EventBus] 总线已连接...
    ```

---

## 4. LLM 客户端 (LLM Client)

为了解耦具体的模型供应商 API，系统实现了统一的 `LLMClient`。

### 4.1 统一接口 (`src.utils.llm_client.LLMClient`)
*   **多供应商支持**: 内部封装了 `openai` (用于 DeepSeek/Qwen) 和 `google.generativeai` (用于 Gemini) 的 SDK。
*   **调用方式**:
    ```python
    client = LLMClient(provider="qwen")
    response = client.chat(messages=[...], model="qwen-turbo")
    ```
*   **自动重试**: 内置了网络错误和限流 (Rate Limit) 的自动重试机制。

---

## 5. 关键代码索引

*   **Settings**: [`src.config.settings.settings.Settings`](../src/config/settings/settings.py)
*   **Logger**: [`src.utils.logger.Logger`](../src/utils/logger.py)
*   **LLM Client**: [`src.utils.llm_client.LLMClient`](../src/utils/llm_client.py)

---

> 文档生成时间: 2026-02-07
> 生成者: XingChen-V (Self-Reflection)
