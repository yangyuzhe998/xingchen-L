# 技能与进化模块详解 (Skills & Evolution Module)

## 1. 进化管理器 (Evolution Manager)

`src/core/evolution_manager.py`

`EvolutionManager` 是系统“自我进化”的核心引擎。它负责将 S脑 的“进化意图”转化为实际可运行的代码。

### 核心工作流

1.  **接收请求**: S脑在 `analyze_cycle` 中输出 `Evolution: [name] - [desc]`。
2.  **生成代码**: 调用 LLM，根据 `docs/dev/skill_standard.md` 规范生成 Python 代码。
3.  **提取与部署**: 解析 LLM 输出，提取代码块，保存为 `src/skills/` 下的 `.py` 文件。
4.  **自动修复**: 如果代码依赖缺失（如 `ImportError`），尝试自动调用 `pip` 安装依赖。
5.  **热加载**: 触发 `SkillLoader` 重新扫描并加载新技能。
6.  **通知**: 向 EventBus/Memory 发送通知，告知系统新技能已就绪。

## 2. 技能加载器 (Skill Loader)

`src/skills/loader.py`

负责动态管理 `src/skills/` 目录下的所有插件。

### 特性

*   **热插拔 (Hot-Swapping)**: 运行时加载新模块，无需重启系统。
*   **多模式支持**:
    *   **单文件模式**: 直接加载 `.py` 文件。
    *   **包模式**: 加载包含 `__init__.py` 的目录。
*   **自动依赖管理**: 遇到 `ModuleNotFoundError` 时尝试自动修复环境。

## 3. 技能开发规范

`docs/dev/skill_standard.md`

所有自动生成的技能必须遵循此规范：

*   **路径**: `src/skills/`
*   **导入**: 必须使用绝对导入 `from src.tools.registry import ...`。
*   **注册**: 必须使用 `@tool_registry.register` 装饰器。
*   **安全**: 禁止高危操作（如删除核心文件），必须包含 `try-except`。

## 4. 示例技能

*   `src/skills/get_weather.py`: 无需 Key 的天气查询工具。
*   `src/skills/qrcode_generator.py`: 二维码生成工具（演示了自动依赖安装）。
*   `src/skills/tool_status_checker.py`: 系统自检工具（S脑自发生成的元认知工具）。
