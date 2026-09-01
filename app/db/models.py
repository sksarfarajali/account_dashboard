from __future__ import annotations

import datetime as dt

from sqlalchemy import DateTime, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        UniqueConstraint("dedupe_key", name="uq_transactions_dedupe_key"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True))
    type: Mapped[str] = mapped_column(String(10))  # "debit" | "credit"
    amount: Mapped[float] = mapped_column(Numeric(12, 2))
    merchant: Mapped[str | None] = mapped_column(String(255), nullable=True)
    account_ref: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source_email_id: Mapped[str] = mapped_column(String(255))
    raw_snippet: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String(50), default="Other")
    dedupe_key: Mapped[str] = mapped_column(String(128), index=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SyncLog(Base):
    __tablename__ = "sync_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    last_sync_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    emails_scanned: Mapped[int] = mapped_column(default=0)
    transactions_added: Mapped[int] = mapped_column(default=0)
