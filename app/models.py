"""ORM 模型定义。

包含用户、挪车码、留言、黑名单以及码级通知偏好等表结构。
字段命名尽量语义化，便于后台检索与导出。
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    """用户表。

    字段：
    - username: 登录名（唯一）
    - email: 邮箱（可选）
    - password_hash: 密码哈希（salt$sha256）
    - status: 账户状态（ACTIVE/…）
    """
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False)
    email = Column(String(120), unique=False, nullable=True)
    password_hash = Column(String(256), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(16), default="ACTIVE")

    codes = relationship("Code", back_populates="owner")


class Code(Base):
    """挪车码表（车主持有）。

    字段：
    - public_code: 用于二维码/落地页的公开 ID（高熵短码）
    - owner_id: 归属用户
    - display_name: 备注/昵称（用于打印展示）
    - status: ACTIVE/PAUSED/DELETED
    """
    __tablename__ = "codes"
    id = Column(Integer, primary_key=True)
    public_code = Column(String(64), unique=True, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    display_name = Column(String(120), nullable=True)
    status = Column(String(16), default="ACTIVE")
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="codes")
    messages = relationship("Message", back_populates="code", cascade="all, delete-orphan")


class Message(Base):
    """留言表（扫码者 -> 车主）。

    字段：
    - sender: 发送方（SCANNER/OWNER 保留）
    - content_text: 文本内容
    - image_path: 图片存储相对路径
    - ip_hash: 基于密钥的 IP 哈希（用于风控/审计）
    - processed: 车主是否标记已处理
    """
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    code_id = Column(Integer, ForeignKey("codes.id"), nullable=False)
    sender = Column(String(16), default="SCANNER")  # SCANNER / OWNER (reserved)
    content_text = Column(Text, nullable=True)
    image_path = Column(String(256), nullable=True)
    ip_hash = Column(String(64), nullable=True)
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    code = relationship("Code", back_populates="messages")


class Blacklist(Base):
    """黑名单表（码级或全局）。

    字段：
    - code_id: 关联的码；为空表示全局
    - ip_hash: 被拉黑的 IP 哈希
    - until: 过期时间（可为空）
    """
    __tablename__ = "blacklist"
    id = Column(Integer, primary_key=True)
    code_id = Column(Integer, ForeignKey("codes.id"), nullable=True)
    ip_hash = Column(String(64), nullable=False)
    reason = Column(String(120), nullable=True)
    until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class CodeNotifyPref(Base):
    """码级通知偏好。

    字段：
    - channel: NONE/BARK（后续可扩展）
    - bark_base_url/bark_token: Bark 所需配置
    - updated_at: 更新时间
    """
    __tablename__ = "code_notify_pref"
    id = Column(Integer, primary_key=True)
    code_id = Column(Integer, ForeignKey("codes.id"), nullable=False)
    channel = Column(String(16), default="NONE")  # NONE / BARK
    bark_base_url = Column(String(256), nullable=True)
    bark_token = Column(String(256), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow)


class AppSetting(Base):
    """全局配置（单行）。

    字段：
    - site_base_url: 站点对外地址（用于二维码链接/打印展示），例如 https://example.com
    """
    __tablename__ = "app_setting"
    id = Column(Integer, primary_key=True)
    site_base_url = Column(String(256), nullable=True)
    site_title = Column(String(256), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow)
