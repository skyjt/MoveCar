2025-08-30
- docs: 同步中文 README 与英文文档
  - 增加 技术栈/你可以做什么/打包/提示与排错 等章节，统一配置与路由说明
  - 关键文件：`readme_zh.md`

2025-08-29
- docs: add English README as default (README.md)
- docs: add Chinese version (readme_zh.md) and cross-link
- docs: reflect latest routes, Docker flow, and config

2025-08-29
- chore: add remote for GitHub repo skyjt/Move_My_Car; push pending auth

2025-08-29
- docs: link Chinese README from main README; add backlink
2025-08-30 docs: add packaging script and .dockerignore; update README
- Added `scripts/package.sh` to generate tar.gz for releases (excludes local-only files)
- Added `.dockerignore` to keep Docker contexts small
- Updated `README.md` with Packaging instructions
- Key files: `scripts/package.sh`, `.dockerignore`, `README.md`

2025-08-30 fix: apply .env admin password changes; auto-load .env
- `bootstrap_admin` now updates existing admin password when `ADMIN_PASSWORD` changes in `.env`/env
- Auto-load `.env` on startup (via `python-dotenv`), and added a fallback minimal parser when the package is missing, so local runs pick up config without manual export
- Updated `requirements.txt` and README local env guidance
- Key files: `app/database.py`, `requirements.txt`, `README.md`

2025-08-30 fix: 登录失败错误信息中文化
- 将登录失败时的错误提示从英文改为中文“用户名或密码错误”，保持返回登录页的交互
- 关键文件：`app/routes/pages.py`

2025-08-30 feat: 页脚版权展示（可自定义 HTML）
- 在所有主要页面增加页脚版权展示，默认包含项目 GitHub 链接
- 在“系统配置”中新增“页脚版权（支持 HTML）”字段，允许自定义任意 HTML 片段
- 数据结构：为 `AppSetting` 增加 `footer_html` 字段，并在启动时自动迁移
- 关键文件：`app/templates/base.html`, `app/templates/landing.html`, `app/templates/print.html`, `app/templates/dashboard.html`, `app/routes/pages.py`, `app/models.py`, `app/database.py`, `README.md`

2025-08-30 docs: 更新 README（技术栈与说明）
- 增加 Tech Stack 段落，微调功能与配置描述
- 关键文件：`README.md`
2025-08-30 docs: 发布 v1.0.0 版本
- 打上 `v1.0.0` 标签并推送至 GitHub（初始稳定版）
- 亮点：挪车码管理、匿名留言（文本+图片）、打印与二维码、Bark 通知、频控与黑名单、可自定义页脚、.env 自动加载与管理员密码变更自动生效
- 关键：请在 GitHub Release 页面从标签创建 Release 并可附上打包产物（dist/*）

2025-08-30 build: 打包脚本支持版本号参数
- `scripts/package.sh vX.Y.Z` 生成 `MoveCar-vX.Y.Z.tar.gz`
- 保留默认 `<timestamp>-<rev>` 命名
- 文档：README Packaging 使用说明已更新
