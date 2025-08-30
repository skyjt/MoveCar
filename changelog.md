2025-08-30
- docs: 同步中文 README 与英文文档
  - 增加 技术栈/你可以做什么/打包/提示与排错 等章节，统一配置与路由说明
  - 关键文件：`readme_zh.md`

2025-08-30
- style: 优化仪表盘滚动背景与页脚视觉
  - 背景使用固定径向渐变叠加底色，滚动不再出现“断层”
  - 页脚统一样式与留白，移除内联样式，支持自定义 HTML
  - 状态中文化并加粗着色：生效（绿色）、失效（红色）；留言“已处理/未处理”同样适配
  - 代码状态改为滑块开关（状态栏内切换），移除“切换启用”按钮
  - 关键文件：`app/style.css`, `app/templates/dashboard.html`, `app/templates/base.html`

2025-08-30
- ui: iOS 风格滑块开关与背景条带优化
  - 将状态开关实现为原生 checkbox + 自定义轨道/圆点，达到 iOS 视觉与动效
  - 为深/浅色背景叠加极低透明度的重复线性纹理，降低渐变条带与滚动断层感知
  - 关键文件：`app/style.css`, `app/templates/dashboard.html`

2025-08-30
- feat(ui/mobile): 仪表盘“我的挪车码”在手机端改为分块展示
  - 名称（标题）/ 状态 / 创建时间 / 操作 / 链接 分行显示，按钮自动换行不再挤在一列
  - 桌面端保留表格，手机端自动隐藏表格并显示分块卡片
  - 关键文件：`app/templates/dashboard.html`, `app/style.css`

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
