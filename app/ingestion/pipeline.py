"""Fetch -> parse -> dedupe -> insert pipeline.

Run as a CLI: python -m app.ingestion.pipeline [--max N]
"""

from __future__ import annotations

import argparse
from email.utils import parsedate_to_datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.categorize.rules import categorize
from app.config.filters import build_gmail_query
from app.db.models import SyncLog, Transaction
from app.db.session import get_session
from app.gmail_client.auth import get_credentials, get_gmail_service
from app.gmail_client.fetch import (
    get_header,
    get_message,
    get_messages_concurrent,
    get_plain_text_body,
    list_message_ids,
)
from app.parsers.registry import parse_email


def sync(max_results: int = 100, service=None, creds=None) -> dict[str, int]:
    """Run a sync.

    - `creds` (a google.oauth2.credentials.Credentials): fetches messages
      concurrently over a small thread pool — much faster for real syncs.
      Both the local CLI and the dashboard pass this.
    - `service` only, no `creds`: fetches sequentially, one request at a
      time. Kept for tests, which mock individual Gmail calls.
    - neither: builds local-flow credentials via get_gmail_service() (file
      token cache) — old default, kept for backward compatibility.
    """
    if service is None and creds is None:
        service = get_gmail_service()
    if service is None:
        from googleapiclient.discovery import build

        service = build("gmail", "v1", credentials=creds, cache_discovery=False)

    query = build_gmail_query()
    message_ids = list_message_ids(service, query=query, max_results=max_results)

    messages = get_messages_concurrent(creds, message_ids) if creds is not None else None

    scanned = 0
    added = 0
    skipped_duplicate = 0
    unparsed = 0

    session = get_session()
    try:
        for msg_id in message_ids:
            scanned += 1
            message = messages[msg_id] if messages is not None else get_message(service, msg_id)
            sender = get_header(message, "From") or ""
            subject = get_header(message, "Subject") or ""
            date_header = get_header(message, "Date")
            body_text = get_plain_text_body(message)

            parsed = parse_email(sender, subject, body_text)
            if parsed is None:
                unparsed += 1
                continue

            if date_header:
                try:
                    parsed.date = parsedate_to_datetime(date_header)
                except (TypeError, ValueError):
                    pass

            dedupe_key = parsed.dedupe_key(source_email_id=msg_id)

            exists = session.execute(
                select(Transaction.id).where(Transaction.dedupe_key == dedupe_key)
            ).first()
            if exists:
                skipped_duplicate += 1
                continue

            txn = Transaction(
                date=parsed.date,
                type=parsed.type,
                amount=parsed.amount,
                merchant=parsed.merchant,
                account_ref=parsed.account_ref,
                source_email_id=msg_id,
                raw_snippet=parsed.raw_snippet,
                category=categorize(parsed.merchant, parsed.raw_snippet),
                dedupe_key=dedupe_key,
            )
            session.add(txn)
            try:
                session.commit()
                added += 1
            except IntegrityError:
                session.rollback()
                skipped_duplicate += 1

        session.add(SyncLog(emails_scanned=scanned, transactions_added=added))
        session.commit()
    finally:
        session.close()

    return {
        "emails_scanned": scanned,
        "transactions_added": added,
        "skipped_duplicate": skipped_duplicate,
        "unparsed": unparsed,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync Gmail transaction alerts into the database.")
    parser.add_argument("--max", type=int, default=100, help="Max emails to scan (default: 100)")
    args = parser.parse_args()

    summary = sync(max_results=args.max, creds=get_credentials())

    print("Sync complete.")
    print(f"  Emails scanned:       {summary['emails_scanned']}")
    print(f"  Transactions added:   {summary['transactions_added']}")
    print(f"  Skipped (duplicate):  {summary['skipped_duplicate']}")
    print(f"  Skipped (unparsed):   {summary['unparsed']}")


if __name__ == "__main__":
    main()
