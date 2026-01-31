# 配置模块详解 (Configuration Module)

## 1. 设置中心 (Settings)

`src/config/settings.py`

集中管理所有硬编码配置和环境变量。

### 关键配置项

*   `PROJECT_ROOT`: 项目根目录绝对路径。
*   `MOLTBOOK_API_KEY`: 社交网络 API Key。
*   `BUS_DB_PATH`: 事件总线数据库路径。
*   `MAX_CODE_SCAN_SIZE`: S脑代码扫描的单文件大小限制 (Default: 50KB)。

## 2. 提示词管理 (Prompt Management)

`src/config/prompts.py`

*   `DRIVER_SYSTEM_PROMPT`: F脑的基础人设和指令。
*   `NAVIGATOR_SYSTEM_PROMPT`: S脑的静态上下文前缀 (包含代码库)。
*   `NAVIGATOR_USER_PROMPT`: S脑的动态输入 (包含交互历史)。

## 3. 环境变量 (.env)

系统启动时会自动通过 `python-dotenv` 加载 `.env` 文件。

**Best Practice**: 代码中严禁出现明文 API Key，必须通过 `settings.py` 或 `os.getenv` 读取。
