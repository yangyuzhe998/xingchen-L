# 服务器部署指南 (Server Deployment Guide)

要想让“星辰-V” 24 小时在线陪伴你，将她部署到云服务器是最好的选择。

> **还没有服务器？** 请先阅读 [服务器购买与避坑指南](server_buying_guide.md)

## 1. 准备工作

### 1.1 购买服务器
*   推荐配置：
    *   **CPU**: 2核 (AI 处理需要一定算力)
    *   **RAM**: 2GB 或以上 (ChromaDB 和 NapCat 都吃内存)
    *   **OS**: Ubuntu 22.04 LTS (最稳)
    *   **网络**: 如果使用 OpenAI/DeepSeek，确保服务器网络能访问这些 API。

### 1.2 安装 Docker (强烈推荐)
在服务器上运行以下命令一键安装 Docker：
```bash
curl -fsSL https://get.docker.com | bash
```

## 2. 部署步骤

### 2.1 上传代码
在服务器上克隆你的代码库：
```bash
git clone https://github.com/yangyuzhe998/xingchen-L.git
cd xingchen-L
```

### 2.2 配置环境
1.  复制环境变量文件：
    ```bash
    cp .env.example .env
    ```
2.  编辑 `.env`，填入你的 API Key：
    ```bash
    vim .env
    ```

### 2.3 启动 NapCat (QQ 客户端)
为了解决 QQ 扫码登录难题，我们使用 `docker-compose`。

1.  编辑 `docker-compose.yml`，把 `ACCOUNT` 换成你的小号 QQ。
2.  启动 NapCat：
    ```bash
    docker compose up -d napcat
    ```
3.  **关键步骤：扫码登录**
    *   查看 NapCat 日志获取二维码：
        ```bash
        docker logs -f napcat
        ```
    *   用手机 QQ 扫码。登录成功后，按 `Ctrl+C` 退出日志查看。

### 2.4 启动星辰-V
一旦 QQ 登录成功，就可以启动主程序了：
```bash
docker compose up -d xingchen
```

## 3. 维护与查看

*   **查看星辰的日志** (看她在想什么)：
    ```bash
    docker logs -f xingchen-v
    ```
*   **重启** (如果她卡住了)：
    ```bash
    docker compose restart xingchen
    ```
*   **更新代码** (当你推送了新功能)：
    ```bash
    git pull
    docker compose build xingchen
    docker compose up -d xingchen
    ```

## 4. 进阶技巧：本地登录，云端运行 (防风控)

如果服务器 IP 登录 QQ 总是提示环境异常，可以在本地电脑上先运行 NapCat 登录成功，然后把生成的 `session.token` 等文件上传到服务器的 `data/napcat/qq` 目录下。
