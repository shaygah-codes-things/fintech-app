from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    ForeignKey,
    DateTime,
    func,
    UniqueConstraint,
)
import sqlalchemy as sa
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.db import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(20))
    provider_user_id: Mapped[str] = mapped_column(String(128), index=True)
    email: Mapped[str | None] = mapped_column(String(255), index=True)
    name: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[DateTime] = mapped_column(
        DateTime, server_default=sa.text("CURRENT_TIMESTAMP")
    )
    __table_args__ = (
        UniqueConstraint("provider", "provider_user_id", name="uniq_identity"),
    )


class Payout(Base):
    __tablename__ = "payouts"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    amount: Mapped[Numeric] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3))
    status: Mapped[str] = mapped_column(
        String(32), default="pending"
    )  # pending|processing|paid|failed
    provider_ref: Mapped[str | None] = mapped_column(String(128), index=True)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime, server_default=sa.text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime,
        server_default=sa.text("CURRENT_TIMESTAMP"),
        onupdate=sa.text("CURRENT_TIMESTAMP"),
    )
    user = relationship("User")


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"
    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    payout_id: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime, server_default=sa.text("CURRENT_TIMESTAMP")
    )


class WebhookEvent(Base):
    __tablename__ = "webhook_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    payload: Mapped[str] = mapped_column(String)
    received_at: Mapped[DateTime] = mapped_column(
        DateTime, server_default=sa.text("CURRENT_TIMESTAMP")
    )
