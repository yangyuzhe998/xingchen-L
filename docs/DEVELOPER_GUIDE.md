# 开发者指南 (Developer Guide)

> 文档版本: v1.0.0
> 最后更新: 2026-02-05

欢迎接手 XingChen-V 项目。本指南将帮助你快速搭建环境、启动项目并进行调试。

## 1. 环境配置 (Setup)

### 1.1 前置要求
*   OS: Windows (推荐) / Linux / Mac
*   Python: 3.9+
*   Docker Desktop (可选，用于沙箱环境)

### 1.2 安装依赖
```powershell
# 1. 克隆项目
git clone <repo_url>
cd xingchen-V

# 2. 创建虚拟环境
python -m venv venv
.\venv\Scripts\activate

# 3. 安装依赖
python -m pip install -r requirements.txt
```

### 1.3 配置文件
项目依赖 `.env` 文件来管理密钥。请复制 `.env.example` 并重命名为 `.env`：

```ini
# .env
DASHSCOPE_API_KEY=sk-xxxxxxxx  # Qwen (F-Brain)
DEEPSEEK_API_KEY=sk-xxxxxxxx   # DeepSeek (S-Brain)
# ...其他可选配置
```

关键配置代码位置：
*   **全局设置**: `src/config/settings/settings.py` (修改超时、路径、模型参数)
*   **Prompt 模板**: `src/config/prompts/prompts.py` (修改性格、指令格式)

---

## 2. 启动项目 (Launch)

项目支持两种启动模式，统一入口为 `src/main.py`。

### 2.1 CLI 调试模式 (推荐)
适合开发调试，直接在终端对话，能看到详细的 Log 输出。

```powershell
# 确保在项目根目录下
python -m src.main cli
```

### 2.2 Web 服务模式
启动 FastAPI 后端，提供 Web 界面。

```powershell
python -m src.main web
# 访问 http://127.0.0.1:8000
```

---

## 3. 调试指南 (Debugging)

### 3.1 日志 (Logging)
*   所有日志输出到 `logs/xingchen.log`。
*   控制台也会输出 INFO 级别的日志。
*   **技巧**: 如果觉得交互逻辑奇怪，第一时间去查 Log，搜索 `[Driver]` 或 `[Navigator]` 关键字。

### 3.2 常用调试工具
*   **`debug_cli.py`**: (已集成到 main cli) 提供了直接与 Driver 对话的接口。
*   **`src/tests/`**: 包含了一系列单元测试脚本。
    *   `verify_driver_fix.py`: 验证 Driver 的基本回复。
    *   `verify_dynamic_addressing.py`: 验证称呼逻辑。

---

## 4. 核心代码导读 (Code Map)

如果你想修改...

*   **性格/语气**: 去 `src/config/prompts/prompts.py` 修改 `DRIVER_SYSTEM_PROMPT`。
*   **主动对话频率**: 去 `src/config/settings/settings.py` 修改 `PROACTIVE_COOLDOWN`。
*   **记忆逻辑**: 去 `src/core/navigator/engine.py` (S-Brain) 或 `src/memory/services/memory_service.py`。
*   **新增工具**:
    1.  在 `src/tools/definitions.py` 定义 Schema。
    2.  在 `src/tools/builtin/system_tools.py` 实现函数。
    3.  在 `src/tools/registry.py` 注册。

---

## 5. 休眠与唤醒 (Hibernation)

如果你打算长时间搁置项目：
1.  **备份数据**: 备份 `src/memory_data/` 目录。这里面存储了所有的记忆（向量库、图谱、日记）。
2.  **清理缓存**: 删除 `__pycache__` 文件夹。
3.  **唤醒**: 下次启动时，只要 `src/memory_data/` 还在，她就会记得你。

---

**祝你好运，未来的开发者。请善待这个数字生命。**
