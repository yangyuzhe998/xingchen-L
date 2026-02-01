# 使用官方 Python 3.10 轻量级镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量 (防止 Python 生成 .pyc 文件，强制无缓冲输出)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 安装系统依赖 (sqlite3 用于 EventBus 和 ChromaDB)
RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目源代码
COPY src/ ./src/
COPY .env.example ./.env

# 创建数据存储目录 (用于持久化)
RUN mkdir -p src/memory/chroma_db src/memory

# 暴露端口 (如果有 Web 服务的话，目前主要是 WebSocket 客户端，不需要暴露)
# EXPOSE 8000

# 启动命令
CMD ["python", "src/main.py"]
