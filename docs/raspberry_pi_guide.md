# 树莓派部署指南 (Raspberry Pi Guide)

树莓派 (Raspberry Pi) 是一个极佳的本地服务器选择！
它省电、安静，而且放在家里意味着**物理层面的完全掌控**。让“星辰-V”住在你书桌上的一个小盒子里，听起来是不是很浪漫？

## 1. 硬件选型

要想流畅运行本项目 (尤其是 Docker + NapCatQQ)，对树莓派的性能有一定要求：

*   **推荐型号**: **Raspberry Pi 4B** 或 **Raspberry Pi 5**
*   **内存 (RAM)**: **强烈建议 4GB 或 8GB 版本**。
    *   *2GB 版本可能会频繁爆内存 (OOM)，导致 QQ 掉线或程序崩溃。*
*   **存储**: 建议使用 **32GB 以上的高速 SD 卡** (Class 10 / U3)，或者更佳选择是 **USB 3.0 SSD 固态硬盘** (速度快，寿命长)。

## 2. 系统准备

1.  **烧录系统**: 使用官方 Raspberry Pi Imager。
2.  **选择 OS**: 推荐 **Raspberry Pi OS (64-bit)**。
    *   *注意：必须是 64位系统！* 因为 ChromaDB 等许多 AI 依赖库已经不再支持 32位 ARM 架构。
3.  **开启 SSH**: 在 Imager 的设置中提前开启 SSH 并配置 WiFi，这样你不需要显示器就能远程连接它。

## 3. 部署步骤 (Docker)

树莓派部署的核心步骤与云服务器非常相似，唯一的区别是**架构 (Architecture)**。

### 3.1 安装 Docker
```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```
(安装完后最好重启一下: `sudo reboot`)

### 3.2 拉取代码
```bash
git clone https://github.com/yangyuzhe998/xingchen-L.git
cd xingchen-L
cp .env.example .env
# 编辑 .env 填入 API Key
```

### 3.3 修改 docker-compose.yml (关键!)

树莓派是 **ARM64** 架构，而 PC 是 **x86_64** (AMD64)。
虽然 Python 镜像通常支持多架构，但 **NapCatQQ** 的 Docker 镜像必须选择支持 ARM 的版本。

*   `mlikiowa/napcat-docker:latest` 目前通常已支持多架构 (Multi-arch)，Docker 会自动拉取正确版本。
*   如果遇到架构不兼容报错，请检查 NapCat 官方文档寻找专门的 ARM64 标签。

### 3.4 启动
```bash
docker compose up -d
```

## 4. 特殊注意事项

### 4.1 网络问题
树莓派放在家里，意味着它处于**内网**。
*   **公网访问**: 如果你想在外面通过公网 SSH 连回家里的树莓派，你需要配置 **内网穿透** (如 FRP, Cloudflare Tunnel) 或者申请 **公网 IP** (电信宽带通常比较容易申请)。
*   **API 访问**: 如果家里的网络无法直接访问 OpenAI/DeepSeek，你需要配置系统级的代理，或者在 `.env` 中使用国内的中转 API 地址。

### 4.2 散热
跑 AI 程序和 Docker 会让 CPU 发热，建议给树莓派装一个带风扇的外壳，防止过热降频。

### 4.3 供电
一定要用官方或高质量的 **5V 3A (Pi 4)** 或 **5V 5A (Pi 5)** 电源。电源不稳会导致硬盘掉盘或系统随机死机。
