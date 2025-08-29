"""数据库初始化与会话管理模块。

职责：
- 根据环境变量 `DB_URL` 创建 SQLAlchemy 引擎；
- 提供 `SessionLocal` 与 `get_db` 依赖；
- 初始化数据表（必要时降级到内存库以适配受限环境）；
- 引导默认管理员账号（`bootstrap_admin`）。
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError
from sqlalchemy import text


DB_URL = os.getenv("DB_URL", "sqlite:///data/app.db")

def _make_engine(url: str):
    """根据 URL 创建引擎。

    sqlite 下关闭 `check_same_thread` 以便 TestClient 多线程使用；
    当使用 `sqlite+pysqlite:///:memory:` 等 URI 形式时启用 `uri` 连接参数。
    """
    if url.startswith("sqlite"):
        # enable cross-thread for TestClient and potential shared memory DB
        connect_args = {"check_same_thread": False, "uri": url.startswith("sqlite+")}
    else:
        connect_args = {}
    return create_engine(url, echo=False, future=True, connect_args=connect_args)


engine = _make_engine(DB_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

Base = declarative_base()


def _reconfigure(url: str):
    """更新全局引擎与会话工厂的绑定。"""
    global engine, SessionLocal, DB_URL
    DB_URL = url
    engine = _make_engine(url)
    SessionLocal.configure(bind=engine)


def init_db():
    """初始化数据表，必要时降级到内存库。

    - 在受限文件系统（只读）时捕获 `OperationalError` 并切换到内存库；
    - 始终调用 `bootstrap_admin` 以保证默认管理员存在。
    """
    # 导入模型以注册元数据
    from . import models  # noqa: F401
    # 重建引擎以拾取可能变更的环境变量（测试友好）
    _reconfigure(DB_URL)
    try:
        Base.metadata.create_all(bind=engine)
    except OperationalError as e:
        msg = str(e).lower()
        if "readonly" in msg or "read-only" in msg:
            # fallback to shared in-memory DB for restricted environments (tests)
            _reconfigure("sqlite+pysqlite:///:memory:?cache=shared")
            Base.metadata.create_all(bind=engine)
        else:
            raise
    # Ensure admin exists (idempotent)
    bootstrap_admin()
    # 轻量迁移：补充 app_setting.site_title 字段（若不存在）
    try:
        with engine.begin() as conn:
            res = conn.execute(text("PRAGMA table_info('app_setting')")).fetchall()
            cols = {r[1] for r in res} if res else set()
            if "site_title" not in cols:
                conn.execute(text("ALTER TABLE app_setting ADD COLUMN site_title VARCHAR(256) NULL"))
    except Exception:
        # 忽略迁移错误以保证启动不中断
        pass


def bootstrap_admin():
    """引导默认管理员：若不存在则创建（幂等）。"""
    from .models import User
    from .utils import hash_password

    username = os.getenv("ADMIN_USERNAME", "admin")
    password = os.getenv("ADMIN_PASSWORD", "admin")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            user = User(username=username, password_hash=hash_password(password))
            db.add(user)
            db.commit()
    finally:
        db.close()


def get_db():
    """FastAPI 依赖：提供一次性数据库会话。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
