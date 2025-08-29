# Move Car 挪车码（开源自部署）

一个开源、可自部署、隐私友好的“公共挪车码”工具。面向个人/社区，无需暴露手机号即可与车主建立匿名联系。MVP 聚焦：挪车码管理、匿名留言（文本+图片）、轻量通知、基础防滥用、打印/电子码。

> English version: see README.md

## 快速开始
- Docker（推荐）
  - 复制配置：`cp .env.example .env`
  - 启动服务：`docker compose up -d`
  - 访问：`http://localhost:8000/login`（默认账户 `admin/admin`）
- 本地开发（不使用 Docker）
  - 创建虚拟环境：`python -m venv .venv && source .venv/bin/activate`
  - 安装依赖：`pip install -r requirements.txt`
  - 可选导入环境：`cp .env.example .env && export $(grep -v '^#' .env | xargs)`
  - 启动开发服务：`uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`
  - 打开：`http://127.0.0.1:8000/login`

## 基本使用
1) 登录后台 → 进入“仪表盘”。
2) 新建挪车码 → 点击“打印 / 下载二维码”查看二维码并下载 PNG；
3) 访客扫码进入 `/c/{public_code}` → 留言（可附 1 张图片 ≤ 5MB）。
4) 车主在仪表盘查看并标记“已处理”。

### 通知设置（Bark）
- 每个挪车码都可单独设置通知：仪表盘 → 目标码 → “通知设置”。
- 渠道：
  - 无：不发送外部推送（默认）。
  - Bark：参考 https://bark.day.app/#/tutorial 获取设备 Token。
- 配置 Bark：
  - 基础 URL：默认 `https://api.day.app`。
  - Token：粘贴 Bark 设备 Token。
  - 保存后可点“发送测试通知”验证。
- 生效时机：访客在落地页留言成功后，会推送“挪车提醒+留言摘要”，并附带仪表盘链接。

## 配置（.env）
- `APP_SECRET`：会话签名密钥（生产请替换）。
- `APP_BASE_URL`：对外访问地址，用于打印页/二维码链接。
- `DB_URL`：数据库 URL，默认 `sqlite:///data/app.db`。
- `DATA_DIR`：数据目录（含上传），默认 `./data`。
- `MAX_IMAGE_MB`：上传图片大小限制（默认 5）。
- `RATE_LIMIT_WINDOW/COUNT`：限流窗口与次数（默认 60 秒 / 1 次）。
- `ANON_CHAT_ENABLED`：是否开启匿名聊天室（MVP 仅留言，默认 false）。
- `ADMIN_USERNAME/ADMIN_PASSWORD`：默认管理员引导账号。

说明：默认使用 SQLite，数据库文件位于 `data/`；图片保存于 `data/uploads/`。Docker 已映射 `./data` 目录，自动持久化。

## 目录结构
- `app/`：后端（FastAPI）与模板（Jinja2）。
- `app/routes/`：页面与 API 路由；`services/`：限流与通知；
- `app/templates/`：页面模板；`app/style.css`、`app/icon.svg`：界面资源。
- `docs/`：文档（`DESIGN.md`、`PRD.md`）。
- `tests/`：pytest 测试。

## 开发与测试
- 开发运行：`uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`
- Docker 日志：`docker compose logs -f app`
- 停止 Docker：`docker compose down`
- 运行测试：`pytest -q`
- 常用路由：
  - 登录：`/login`；仪表盘：`/dashboard`
  - 扫码落地页：`/c/{public_code}`
  - 打印页面：`/print/{public_code}`（包含下载按钮）
  - 直接二维码：`/qr/{public_code}.png?scale=10&border=2`
  - 通知设置页：`/codes/{id}/notify`

## 文档与计划
- 需求：`docs/PRD.md`
- 设计：`docs/DESIGN.md`
- 规划：通知适配器（Email/Telegram/NTFY）、家庭共享同一码、一次性码/有效期、国际化、PWA、可选 WebRTC 语音。

## 部署与安全建议
- 生产建议开启 HTTPS（Caddy/Nginx 反代）。
- 修改 `APP_SECRET` 与默认管理员密码，持久化 `data/` 目录（数据库与图片）。
- Bark 推送异常请检查基础 URL、Token 与网络连通性，并查看返回的 HTTP 状态码与内容。
