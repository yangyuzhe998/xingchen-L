# 部署指南 (Deployment Guide)

## 1. Windows 本地部署 (推荐)

这是目前最稳定、调试最方便的运行方式。

### 1.1 环境准备
1.  **安装 Python**: 确保安装了 Python 3.10 或更高版本。
2.  **安装依赖**:
    在项目根目录下打开终端 (CMD 或 PowerShell)，运行：
    ```bash
    python -m pip install -r requirements.txt
    ```
    *注意：如果遇到 pip 错误，请尝试 `python -m pip install --upgrade pip` 更新 pip。*

### 1.2 配置
1.  复制 `.env.example` 为 `.env`。
2.  编辑 `.env` 文件，填入必要的 API Key (如 DeepSeek, OpenAI 等)。

### 1.3 启动
在项目根目录下运行：
```bash
python -m src.main
```

### 1.4 常见问题
*   **ChromaDB 安装失败**: Windows 上可能需要安装 Visual C++ Build Tools。如果遇到问题，尝试 `python -m pip install chromadb` 单独安装查看错误详情。
*   **PowerShell 运行错误**: 建议使用 `python -m src.main` 这种标准方式启动，避免路径问题。

## 2. 记忆系统 (Memory)
本项目默认启用完整记忆系统 (Full Mode)，包含：
*   **短期记忆**: 内存中的对话上下文。
*   **长期记忆**: 基于 ChromaDB 的向量数据库，用于存储事实和重要信息。
    *   数据存储位置: `src/memory/chroma_db`
    *   *注意：首次运行时会自动下载 embedding 模型，可能需要一点时间。*

## 3. 其他平台
*   **NAS / Docker**: 目前已暂停维护 NAS 和 Docker 部署方案，建议优先使用 Windows 本地运行。
