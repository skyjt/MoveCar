# Move Car 挪车码（开源自部署）

一个开源、可自部署、隐私友好的“公共挪车码”工具。面向个人/社区，无需暴露手机号即可与车主建立匿名联系。MVP 聚焦：挪车码管理、匿名留言（文本+图片）、站内提醒、基础防滥用、打印/电子码。

## 快速开始
- Docker（推荐）
  - 复制配置：`cp .env.example .env`
  - 启动服务：`docker compose up -d`
  - 访问：`http://localhost:8000/login`（默认账户 `admin/admin`）
- 本地开发运行（不使用 Docker）
  - 创建虚拟环境：`python -m venv .venv && source .venv/bin/activate`
  - 安装依赖：`pip install -r requirements.txt`
  - 可选导入环境：`cp .env.example .env && export $(grep -v '^#' .env | xargs)`
  - 启动开发服务：`uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`
  - 打开：`http://127.0.0.1:8000/login`

## 基本使用
1) 登录 → 进入“仪表盘”。
2) 新建挪车码 → 点击“打印 / 下载二维码”查看二维码并下载 PNG；
3) 访客扫码进入 `/c/{public_code}` → 留言（可附 1 张图片 ≤5MB）。
4) 车主在仪表盘查看、回复（站内）、标记“已处理”。

### 通知设置（Bark）
- 每个挪车码都可单独设置通知：仪表盘 → 目标码 → “通知设置”。
- 渠道：
  - 无：不发送 Webhook 通知（默认）。
  - Bark：参考教程 https://bark.day.app/#/tutorial 在 Bark App 获取 Token。
- 配置 Bark：
  - 基础 URL：默认 `https://api.day.app`（可保留）。
  - Token：粘贴 Bark 设备 Token。
  - 保存后可点“发送测试通知”验证（成功将收到一条“测试通知”）。
- 生效时机：访客在落地页留言成功后，会推送“挪车提醒+留言摘要”，并附带仪表盘链接。
- 关闭通知：将渠道改为“无”并保存。

## 配置（.env）
- `APP_SECRET`：会话签名密钥（请在生产替换）。
- `APP_BASE_URL`：外部访问地址，用于打印页链接。
- `MAX_IMAGE_MB`：上传图片大小（默认 5）。
- `RATE_LIMIT_WINDOW/COUNT`：限流窗口与次数（默认 60 秒/1 次）。
- `ANON_CHAT_ENABLED`：是否开启匿名聊天室（MVP 仅留言，默认 false）。
- `ADMIN_USERNAME/ADMIN_PASSWORD`：默认管理员。

说明：无需配置数据库，默认使用 `data/app.db`（SQLite）；上传图片存储在 `data/uploads/`。Docker 已映射 `./data` 目录，自动持久化数据库与图片。

## 目录结构
- `app/`：后端（FastAPI）与模板（Jinja2）。
- `app/routes/`：页面与 API 路由；`services/`：限流等；`uploads/`：图片上传。
- `docs/`：文档（`DESIGN.md` 设计文档）。
- `PRD.md`：需求文档；`tests/`：pytest 测试。

## 开发与测试
- 启动（开发）：`uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`
- 查看日志（Docker）：`docker compose logs -f app`
- 停止（Docker）：`docker compose down`
- 运行测试：`pytest -q`
- 关键端点：
  - 登录页：`/login`；仪表盘：`/dashboard`
  - 扫码落地页：`/c/{public_code}`
  - 打印/下载：`/print/{public_code}`（内含下载按钮）
  - 直接二维码：`/qr/{public_code}.png?scale=10&border=2`
  - 通知设置页面：`/codes/{id}/notify`（后台点击入口跳转）

## 文档与路线
- 需求：`PRD.md`
- 设计：`docs/DESIGN.md`
- 后续计划：通知适配器（Email/Telegram/NTFY）、共享同一码、一次性码、国际化、PWA、WebRTC 语音等。

提示
- 若出现“attempt to write a readonly database”，请确认当前目录可写或设置 `DB_URL=sqlite:///./data/dev.db`；
- 首次运行会自动创建 `data/` 与 `data/uploads/` 目录；
- 生成二维码依赖 `segno`（已包含）、PNG 写出依赖 `pypng`（已包含）。生产部署请开启 HTTPS，并修改 `APP_SECRET` 与管理员密码；同时持久化 `data/` 目录（包含数据库与图片）。
- Bark 推送失败排查：检查基础 URL 是否可达、Token 是否正确、服务器是否能访问外网（防火墙/代理），以及返回的 HTTP 状态码与报错信息。
