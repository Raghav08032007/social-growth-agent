import time
import uuid

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def new_id():
    return uuid.uuid4().hex


def timestamp():
    return int(time.time())


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(120))
    is_staff: Mapped[bool] = mapped_column(Boolean, default=False)


class Workspace(Base):
    __tablename__ = "workspaces"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(120))
    plan_price_paise: Mapped[int] = mapped_column(BigInteger, default=149900)
    cost_alert_percent: Mapped[int] = mapped_column(Integer, default=30)


class Membership(Base):
    __tablename__ = "memberships"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), primary_key=True)
    role: Mapped[str] = mapped_column(String(20), default="owner")


class SessionToken(Base):
    __tablename__ = "sessions"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    expires_at: Mapped[int] = mapped_column(BigInteger)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)


class TenantRecord:
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    created_at: Mapped[int] = mapped_column(BigInteger, default=timestamp)


class FeatureFlag(TenantRecord, Base):
    __tablename__ = "feature_flags"
    __table_args__ = (UniqueConstraint("workspace_id", "name"),)
    name: Mapped[str] = mapped_column(String(80))
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)


class VaultToken(TenantRecord, Base):
    __tablename__ = "vault_tokens"
    __table_args__ = (UniqueConstraint("workspace_id", "provider", "account_id"),)
    provider: Mapped[str] = mapped_column(String(40))
    account_id: Mapped[str] = mapped_column(String(120))
    envelope: Mapped[dict] = mapped_column(JSON)
    scopes: Mapped[list] = mapped_column(JSON)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)


class AgentAction(TenantRecord, Base):
    __tablename__ = "agent_actions"
    action: Mapped[str] = mapped_column(String(100))
    actor_id: Mapped[str] = mapped_column(String(40))
    entity_id: Mapped[str] = mapped_column(String(40))


class CreditEntry(TenantRecord, Base):
    __tablename__ = "credits_ledger"
    __table_args__ = (UniqueConstraint("workspace_id", "operation_key"),)
    operation_key: Mapped[str] = mapped_column(String(100))
    amount_paise: Mapped[int] = mapped_column(BigInteger)
    category: Mapped[str] = mapped_column(String(40))


class Job(TenantRecord, Base):
    __tablename__ = "job_log"
    __table_args__ = (UniqueConstraint("workspace_id", "idempotency_key"),)
    idempotency_key: Mapped[str] = mapped_column(String(100))
    kind: Mapped[str] = mapped_column(String(80))
    payload: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20), default="queued", index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    available_at: Mapped[int] = mapped_column(BigInteger, default=timestamp, index=True)
    lease_until: Mapped[int] = mapped_column(BigInteger, default=0)
    lease_token: Mapped[str | None] = mapped_column(String(32))
    last_error: Mapped[str | None] = mapped_column(Text)
