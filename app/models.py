from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def uid():
    return str(uuid4())


def now():
    return datetime.now(timezone.utc).timestamp()


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(16), default="user")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    approved: Mapped[bool] = mapped_column(Boolean, default=False)
    daily_requests: Mapped[int | None] = mapped_column(Integer)
    daily_units: Mapped[int | None] = mapped_column(Integer)
    max_concurrent: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[float] = mapped_column(default=now)


class RoleBudget(Base):
    __tablename__ = "role_budgets"
    role: Mapped[str] = mapped_column(String(16), primary_key=True)
    daily_requests: Mapped[int] = mapped_column(default=100)
    daily_units: Mapped[int] = mapped_column(default=50000)
    max_concurrent: Mapped[int] = mapped_column(default=1)
    max_output: Mapped[int] = mapped_column(default=512)
    model_enabled: Mapped[bool] = mapped_column(default=True)


class Family(Base):
    __tablename__ = "sessions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    revoked: Mapped[bool] = mapped_column(default=False)
    expires_at: Mapped[float]


class Refresh(Base):
    __tablename__ = "refresh_tokens"
    digest: Mapped[str] = mapped_column(String(64), primary_key=True)
    family_id: Mapped[str] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), index=True
    )
    used: Mapped[bool] = mapped_column(default=False)


class Recovery(Base):
    __tablename__ = "recovery_tokens"
    digest: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    expires_at: Mapped[float]
    used: Mapped[bool] = mapped_column(default=False)


class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(100), default="New conversation")
    created_at: Mapped[float] = mapped_column(default=now)


class Message(Base):
    __tablename__ = "messages"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[float] = mapped_column(default=now)


class Generation(Base):
    __tablename__ = "generations"
    __table_args__ = (UniqueConstraint("user_id", "request_key"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )
    request_key: Mapped[str] = mapped_column(String(64))
    message_id: Mapped[str] = mapped_column(ForeignKey("messages.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(16), default="streaming")
    reserved_units: Mapped[int]
    actual_tokens: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[float] = mapped_column(default=now)
    expires_at: Mapped[float]
    cancel_requested: Mapped[bool] = mapped_column(default=False)


class DailyUsage(Base):
    __tablename__ = "daily_usage"
    __table_args__ = (UniqueConstraint("user_id", "day"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    day: Mapped[str] = mapped_column(String(10))
    requests: Mapped[int] = mapped_column(default=0)
    units: Mapped[int] = mapped_column(default=0)


class Throttle(Base):
    __tablename__ = "throttles"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    count: Mapped[int] = mapped_column(default=1)
    expires_at: Mapped[float]


class Audit(Base):
    __tablename__ = "audit_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    actor_id: Mapped[str] = mapped_column(String(36))
    action: Mapped[str] = mapped_column(String(64))
    target_id: Mapped[str] = mapped_column(String(36))
    created_at: Mapped[float] = mapped_column(default=now)
