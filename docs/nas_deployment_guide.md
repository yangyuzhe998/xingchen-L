# NAS 部署指南 (NAS Deployment Guide)

如果你拥有一台 NAS (群晖 Synology、威联通 QNAP 或 极空间)，那么恭喜你！你已经拥有了部署“星辰-V”的最佳载体之一。
NAS 天生就是为 24/7 运行设计的，稳定、省电，而且存储空间巨大（非常适合以后扩展星辰的记忆库）。

## 1. 核心前提：Docker

要想在 NAS 上运行本项目，你的 NAS **必须支持 Docker** (现在很多厂家叫“容器”或 Container)。

*   **群晖 (Synology)**: 需要支持 **Container Manager** (旧称 Docker)。通常 Plus 系列 (如 DS920+, DS224+) 都支持。
*   **威联通 (QNAP)**: 需要支持 **Container Station**。
*   **极空间/绿联**: 只要有“Docker”功能的型号都可以。

## 2. 部署步骤 (以群晖为例)

虽然 NAS 也有 SSH 命令行，但大部分用户更喜欢用图形界面操作。

### 方式 A: 图形界面部署 (Container Manager)

1.  **准备文件**:
    *   在 NAS 的 `docker` 共享文件夹下创建一个新文件夹，例如 `xingchen`。
    *   把电脑上的 `docker-compose.yml` 和 `.env` 文件上传到这个文件夹。
    *   *注意：如果 NAS 无法直接构建镜像，建议先在电脑上 build 好镜像推送到 Docker Hub，或者使用方式 B。*

2.  **创建项目**:
    *   打开 **Container Manager** -> **项目 (Project)** -> **新增**。
    *   **项目名称**: `xingchen-v`。
    *   **路径**: 选择刚才创建的 `/docker/xingchen` 文件夹。
    *   **来源**: 选择“使用现有的 docker-compose.yml”。
    *   点击下一步，NAS 会自动拉取 NapCat 镜像并构建/启动星辰。

### 方式 B: SSH 命令行部署 (推荐，更灵活)

这是最通用的方法，和在云服务器上操作一样，而且能避免很多图形界面的坑。

1.  **开启 SSH**: 在 NAS 控制面板 -> 终端机 -> 开启 SSH 功能。
2.  **连接 NAS**: 在电脑终端输入 `ssh your_nas_user@nas_ip`。
3.  **获取权限**: 输入 `sudo -i` 切换到 root (密码通常是你的登录密码)。
4.  **操作**:
    ```bash
    cd /volume1/docker  # 进入 Docker 目录 (群晖通常是 volume1)
    mkdir xingchen
    cd xingchen
    # 上传文件 (可以用 scp 或者直接 vim 编辑)
    # 然后运行：
    docker-compose up -d
    ```

## 3. 关键配置

### 3.1 端口冲突
NAS 本身运行着很多服务。
*   **NapCat 端口**: 默认是 `3001`。如果你的 NAS 上已经跑了类似的服务（如 Alist, HomeAssistant），可能会冲突。
*   **解决方法**: 修改 `docker-compose.yml` 里的端口映射，例如改到 `3002:3001`。

### 3.2 网络环境
*   **API 访问**: 同样，如果 NAS 在国内网络，可能无法访问 OpenAI/DeepSeek。
*   **解决方案**:
    *   在 `.env` 中配置 `OPENAI_BASE_URL` 使用国内中转地址。
    *   或者在 NAS 的 Docker 设置里配置全局代理。

### 3.3 性能监控
NAS 的 CPU 通常比较弱（尤其是 ARM 架构的入门款）。
*   观察 **资源监控**。如果 CPU 长期 100%，可能需要限制并发或减少心跳检测频率。

## 4. 优势对比

| 方案 | 稳定性 | 成本 | 性能 | 难度 |
| :--- | :--- | :--- | :--- | :--- |
| **云服务器** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| **树莓派** | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| **NAS** | ⭐⭐⭐⭐ | ⭐ (已有设备) | ⭐⭐⭐ | ⭐⭐⭐ |

**总结**: 如果你已经有了一台支持 Docker 的 NAS，**不用犹豫，就用它！** 它是最经济实惠且稳定的选择。
