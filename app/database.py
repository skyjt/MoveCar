"""数据库初始化与会话管理模块。

职责：
- 根据环境变量 `DB_URL` 创建 SQLAlchemy 引擎；
- 提供 `SessionLocal` 与 `get_db` 依赖；
- 初始化数据表（必要时降级到内存库以适配受限环境）；
- 引导默认管理员账号（`bootstrap_admin`）。

变更说明：
- 自动加载项目根目录下的 `.env`（若安装了 `python-dotenv`），便于本地开发无需手动 `export`；
- `bootstrap_admin` 现在会在检测到环境变量中的管理员密码变更时，自动更新现有管理员的密码哈希，确保修改 `.env` 后生效。
"""

import os
from pathlib import Path

def _load_env():
    """加载 .env 文件。

    优先使用 python-dotenv；若未安装，则采用简易解析器作为降级方案。
    降级方案仅在环境变量未设置时填充，避免覆盖显式导出的变量。
    """
    # 计算仓库根目录（app/ 的父目录）
    try:
        repo_root = Path(__file__).resolve().parents[1]
    except Exception:
        repo_root = Path.cwd()
    env_path = repo_root / ".env"

    # 尝试使用 python-dotenv（若可用）
    try:
        from dotenv import load_dotenv  # type: ignore

        # 为了不意外覆盖显式导出的系统变量，这里保持 override=False
        load_dotenv(dotenv_path=str(env_path), override=False)
        return
    except Exception:
        pass

    # 简易降级：仅当键不存在于环境变量时才从 .env 填充
    if env_path.exists():
        try:
            for line in env_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k, v = k.strip(), v.strip()
                if k and (k not in os.environ):
                    os.environ[k] = v
        except Exception:
            # 忽略降级读取中的异常，保证应用可继续运行
            pass


# 模块导入即加载 .env（若存在）
_load_env()
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
    # 轻量迁移：补充 app_setting.site_title / footer_html 字段（若不存在）
    try:
        with engine.begin() as conn:
            res = conn.execute(text("PRAGMA table_info('app_setting')")).fetchall()
            cols = {r[1] for r in res} if res else set()
            if "site_title" not in cols:
                conn.execute(text("ALTER TABLE app_setting ADD COLUMN site_title VARCHAR(256) NULL"))
            if "footer_html" not in cols:
                conn.execute(text("ALTER TABLE app_setting ADD COLUMN footer_html TEXT NULL"))
    except Exception:
        # 忽略迁移错误以保证启动不中断
        pass


def bootstrap_admin():
    """引导默认管理员：若不存在则创建；若存在且密码与环境变量不匹配则更新。

    设计意图：
    - 许多用户在 `.env` 中调整 `ADMIN_PASSWORD`，期望重启后立即生效；
    - 之前逻辑仅在“管理员不存在”时创建，导致修改密码不生效；
    - 现逻辑在管理员已存在时会比对环境变量密码，若不匹配则刷新密码哈希。
    """
    from .models import User
    from .utils import hash_password, verify_password

    username = os.getenv("ADMIN_USERNAME", "admin")
    password = os.getenv("ADMIN_PASSWORD", "admin")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            # 不存在则创建默认管理员
            user = User(username=username, password_hash=hash_password(password))
            db.add(user)
            db.commit()
        else:
            # 已存在则校验密码是否与环境变量一致，不一致则更新（支持 .env 修改后生效）
            if password and not verify_password(password, user.password_hash):
                user.password_hash = hash_password(password)
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
