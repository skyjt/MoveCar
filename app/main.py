"""应用入口模块。

职责：
- 创建 FastAPI 应用并挂载静态资源；
- 配置会话中间件（使用 `APP_SECRET`）；
- 初始化数据库与默认管理员；
- 注册页面路由与 API 路由。

说明：在 `create_app` 中调用 `init_db()` 方便测试环境直接使用 TestClient。
"""

import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from .database import init_db
from .utils import ensure_dirs
from .routes import pages as pages_routes
from .routes import api as api_routes


def create_app() -> FastAPI:
    """创建并返回 FastAPI 应用实例。"""
    app = FastAPI(title="Move Car - Open Source")

    # static mounts
    data_dir, uploads_dir = ensure_dirs()
    # 静态资源：/static 用于前端样式与模板资源；/media 用于用户上传图片
    app.mount("/static", StaticFiles(directory="app"), name="static")
    app.mount("/media", StaticFiles(directory=uploads_dir), name="media")

    # sessions
    secret = os.getenv("APP_SECRET", "change-me")
    app.add_middleware(SessionMiddleware, secret_key=secret)

    # 初始化数据库与默认管理员（便于测试直连，不依赖 lifespan 事件）
    init_db()

    # routes
    app.include_router(pages_routes.router)
    app.include_router(api_routes.router)

    return app


app = create_app()
