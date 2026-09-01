from __future__ import annotations

import datetime as dt

import pandas as pd
from sqlalchemy import text

from app.db.session import engine


def load_transactions(start: dt.date | None = None, end: dt.date | None = None) -> pd.DataFrame:
    query = "SELECT id, date, type, amount, merchant, account_ref, category, raw_snippet FROM transactions"
    params: dict[str, object] = {}
    clauses = []
    if start:
        clauses.append("date >= :start")
        params["start"] = start
    if end:
        clauses.append("date <= :end")
        params["end"] = end
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY date DESC"

    df = pd.read_sql(text(query), engine, params=params)
    if not df.empty:
        df["amount"] = df["amount"].astype(float)
        df["date"] = pd.to_datetime(df["date"])
    return df


def update_category(transaction_id: int, category: str) -> None:
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE transactions SET category = :category WHERE id = :id"),
            {"category": category, "id": transaction_id},
        )


def last_sync_summary() -> dict | None:
    query = text(
        "SELECT last_sync_at, emails_scanned, transactions_added "
        "FROM sync_log ORDER BY last_sync_at DESC LIMIT 1"
    )
    with engine.connect() as conn:
        row = conn.execute(query).mappings().first()
    return dict(row) if row else None
