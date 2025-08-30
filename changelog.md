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

2025-08-30 fix(test): 测试环境下避免 .env 干扰管理员密码
- 默认不再在代码中自动加载 `.env`；如需启用，设置 `LOAD_ENV_FILE=1`
- `bootstrap_admin` 在 pytest/测试库(`test.db`) 环境下强制使用 `admin/admin`，避免宿主 `.env` 覆盖单测默认值
- 关键文件：`app/database.py`

2025-08-30 refactor: 轻度清理与注释优化
- 去除未使用的导入（`app/main.py`）
- 简化时间格式化实现，移除不必要的 `pytz` 依赖路径（函数内部保护性处理）
- 小幅中文注释补充与健壮性兜底
- 关键文件：`app/main.py`, `app/routes/pages.py`

2025-08-30 docs: 重写与完善 README（中英）与根 PRD
- README：补充完整技术栈、配置、开发与测试指引、安全注意事项、故障排查
- 中文 README 同步；新增根目录 `PRD.md` 指向 `docs/PRD.md`
- 关键文件：`README.md`, `readme_zh.md`, `PRD.md`

2025-08-30 refactor: 适配 Starlette 模板新签名，消除弃用告警
- 将 `templates.TemplateResponse(name, {"request": request, ...})` 改为 `templates.TemplateResponse(request, name, {...})`
- 关键文件：`app/routes/pages.py`

2025-08-30 chore(security): 从仓库移除本地 `.env`（已在 .gitignore）
- 防止误提交敏感信息，后续请基于 `.env.example` 配置
- 关键：本次仅移除工作区文件，不影响历史提交记录

2025-08-30 feat(ux): 开关“启用/暂停”支持局部刷新（AJAX）
- 新增 API：`POST /api/v1/codes/{id}/toggle` 返回 JSON 状态
- 仪表盘开关改为使用 fetch 局部更新，保留无 JS 的表单回退
- 关键文件：`app/routes/api.py`, `app/templates/dashboard.html`
