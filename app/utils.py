"""通用工具函数集合。

包含密码哈希、随机短码生成、IP 哈希以及目录初始化等工具。
注：密码哈希采用 salt + sha256 的简单方案（便于自部署）；
生产环境可替换为 BCrypt/Argon2 以获得更强强度。
"""

import os
import hashlib
import secrets
from typing import Tuple


def hash_password(password: str, salt: str | None = None) -> str:
    """计算密码哈希（salt$sha256）。"""
    if salt is None:
        salt = secrets.token_hex(16)
    data = (salt + password).encode("utf-8")
    digest = hashlib.sha256(data).hexdigest()
    return f"{salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    """校验明文密码是否匹配存储哈希。"""
    try:
        salt, digest = stored.split("$", 1)
    except ValueError:
        return False
    return hash_password(password, salt) == stored


def generate_public_code() -> str:
    """生成 URL 安全的高熵短码（约 10 字符）。"""
    return secrets.token_urlsafe(8)


def hash_ip(ip: str) -> str:
    """对 IP 基于 APP_SECRET 进行哈希（仅用于风控/审计，不可逆）。"""
    secret = os.getenv("APP_SECRET", "")
    return hashlib.sha256((secret + "|" + ip).encode("utf-8")).hexdigest()


def ensure_dirs():
    """确保数据目录与上传目录存在，返回二者路径。

    注意：
    - 将 SQLite 数据与上传的图片统一放在 `data/` 目录下，便于 Docker 映射持久化；
    - 上传目录固定为 `data/uploads`。
    """
    data_dir = os.getenv("DATA_DIR", "./data")
    uploads_dir = os.path.join(data_dir, "uploads")
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(uploads_dir, exist_ok=True)
    return data_dir, uploads_dir
