# Move Car 挪车码（开源自部署）设计文档（MVP）

基于需求文档（参见仓库 `PRD.md`）的第一版实现设计，目标是自部署、轻依赖、优先落地基础功能：挪车码管理、匿名文本沟通/留言、站内提醒、基础防滥用、Docker 启动。

## 一、技术选型

- 后端：Python 3.12 + FastAPI（API 与 WebSocket） + Uvicorn（ASGI）。
- 数据：SQLite（默认，内嵌单文件）；SQLAlchemy 2.x（ORM）/Alembic（迁移，可选）。
- 前端：服务端模板 Jinja2 + 少量原生 JS（或 Alpine.js/HTMX，择一）；不引入重型框架。
- 实时：FastAPI WebSocket（匿名会话通道）；SSE 可作为备用（降级）。
- 静态/上传：本地文件系统（`uploads/` 目录），图片单文件 ≤ 5MB，类型限制 jpg/png/webp。
- 身份与会话：本地账户（用户名/邮箱 + 密码，BCrypt）；基于签名 Cookie 的会话（`itsdangerous`）。
- 部署：Docker + Docker Compose；可选 Caddy/Nginx 反向代理启用 HTTPS。

## 二、系统架构（MVP）

- 组件：
  - Web/API：路由、模板渲染、REST API、WebSocket；
  - 会话与留言：房间管理（内存管理 + DB 落盘）、消息投递、超时回收；
  - 限流与风控：基于 IP+code 的滑动窗口计数（SQLite/内存）+ 可选验证码；
  - 媒体与静态：图片存储、访问鉴权（仅留言图片可直接读取，带伪随机文件名）；
  - 站内提醒：未读计数、轮询接口（或轻量 WebSocket 推送）。
- 进程：单进程/单实例即可；后续可通过反向代理与多副本扩展（非 MVP 目标）。

## 三、数据模型（简化）

- User：`id, username, email?, password_hash, created_at, status`
- Code：`id (高熵), owner_id, display_name?, status(ACTIVE/PAUSED/DELETED), created_at`
- Session：`id, code_id, status(OPEN/CLOSED/EXPIRED), expire_at, created_at`
- Message：`id, session_id, sender(OWNER/SCANNER), content_text?, image_path?, created_at`
- Blocklist：`id, scope(GLOBAL/CODE), code_id?, ip_hash?, fp_hash?, reason, until`
- RateLog（简化实现可不建表，内存窗口即可）：`ip, code_id, ts`

索引建议：

- `idx_code_owner`，`idx_session_codeid_created_at`，`idx_msg_sessionid_created_at`，`idx_block_until`

## 四、接口与路由（MVP）

- 页面：
  - `GET /login` 登录；`POST /login`；`POST /logout`
  - `GET /dashboard` 车主管理台（码列表、消息/留言入口）
  - `GET /codes/new` 新建码；`POST /codes` 创建；`POST /codes/{id}/toggle` 启用/停用
  - `GET /c/{code}` 扫码落地页（匿名聊天/留言）
  - `GET /print/{code}` 打印页（渲染 QR + 说明）
- API（JSON）：
  - `GET /api/v1/codes` 列码；`POST /api/v1/codes` 新建；`DELETE /api/v1/codes/{id}` 删除
  - `GET /api/v1/sessions?code=...` 获取或创建会话（若开启匿名聊天室）
  - `POST /api/v1/messages` 发送留言（含可选图片）
  - `GET /api/v1/inbox` 未读摘要/列表；`POST /api/v1/messages/{id}/mark` 标记处理
  - `POST /api/v1/blocklist` 黑名单增删改
- WebSocket：
  - `WS /ws/session/{session_id}` 双向文本消息（匿名会话）；超时自动关闭（默认 24h）

说明：如首版仅做“留言 + 站内提醒”，可不实现 WebSocket 与 `Session` 实时通道。

## 五、页面与交互（最小化）

- 落地页（`/c/{code}`）：
  - 展示码备注与隐私提示；
  - 文本输入框 + 可选图片上传（1 张）；
  - 提交后显示“已送达/等待车主回复/可稍后查看”。
- 车主管理台：
  - 码列表（创建、启用/停用、打印链接）；
  - 消息/留言列表（未读在前）；回复输入框；状态标记按钮。

## 六、限流与黑名单（简化）

- 限流：同 IP + 同 code 的滑动窗口（默认：60 秒最多 1 次提交），内存计数并周期性落盘（或直接 SQLite 聚合）。
- 验证码：仅在触发频控后展示（开关可配，默认关闭）。
- 黑名单：
  - 码级黑名单：由车主在管理台对可疑 IP/指纹添加；
  - 全局黑名单：管理员维护；
  - 命中即拒绝提交。

## 七、配置与常量

- `.env` 示例：
  - `APP_SECRET`（会话签名密钥）
  - `APP_BASE_URL`（对外访问域名，用于二维码生成）
  - `DB_URL`（默认 `sqlite:///data/app.db`）
  - `DATA_DIR`（默认 `./data`，含 `uploads/`）
  - `MAX_IMAGE_MB`（默认 5）
  - `RATE_LIMIT_WINDOW=60`、`RATE_LIMIT_COUNT=1`
  - `ANON_CHAT_ENABLED=true|false`（是否开启匿名聊天室）

## 八、目录结构（建议）

```
/(repo)
├─ app/
│  ├─ main.py           # FastAPI 入口
│  ├─ deps.py           # 依赖与鉴权
│  ├─ models.py         # ORM 模型
│  ├─ schemas.py        # Pydantic 模型
│  ├─ routes/
│  │   ├─ pages.py      # 页面路由
│  │   ├─ api.py        # REST API
│  │   └─ ws.py         # WebSocket
│  ├─ services/
│  │   ├─ codes.py      # 挪车码逻辑
│  │   ├─ messages.py   # 留言/会话逻辑
│  │   └─ rate_limit.py # 限流
│  ├─ templates/        # Jinja2 模板
│  ├─ static/           # 静态资源
│  └─ uploads/          # 图片上传（持久化卷）
├─ data/                # SQLite 与持久化目录（挂卷）
├─ docker-compose.yml
├─ .env.example
└─ docs/
   └─ DESIGN.md
```

## 九、部署与运行

- Docker Compose（示例）：
  - 单服务容器运行 `uvicorn app.main:app --host 0.0.0.0 --port 4000`；
  - 将 `./data` 与 `./app/uploads` 映射为持久化卷；
- 反向代理：Caddy/Nginx 提供 TLS，转发 `/` 与 `/ws`；
- 启动流程：复制 `.env.example` → 编辑必要项 → `docker compose up -d`。

## 十、测试与验收（MVP）

- 手工流：创建码 → 打印页查看二维码 → 扫码发送留言 → 车主端看到并回复 → 标记已处理。
- 限流：同 IP 连续提交触发限制；
- 黑名单：命中后提交被拒；
- 上传：非图片/超大小被拒；
- 持久化：容器重启后数据仍可见。

## 十一、迭代路线（与需求对应）

- P1：
  - 通知适配器（Email/Telegram/NTFY 其一）；
  - 家庭共享同一码；
  - 一次性码/电子码有效期；
  - 国际化与 PWA（可选）。
- P2：
  - WebRTC 语音（点对点，附 TURN 示例）；
  - 审计导出、主题定制、批量导入/NFC、社区多租户。

附：若首版选择“仅留言 + 站内提醒”，删除本设计中的 WebSocket、Session 实时通道与相关页面交互，其他保持不变即可。
