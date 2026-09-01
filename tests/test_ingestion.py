"""Integration test for the ingestion pipeline against a real Postgres DB
(the one configured via DATABASE_URL), with the Gmail API layer mocked out.
Cleans up every row it inserts.
"""

from unittest.mock import patch

from sqlalchemy import delete

from app.db.models import SyncLog, Transaction
from app.db.session import get_session
from app.ingestion.pipeline import sync

FAKE_MESSAGE_ID = "test-msg-hdfc-001"

FAKE_MESSAGE = {"id": FAKE_MESSAGE_ID}

FAKE_HEADERS = {
    "From": "alerts@hdfcbank.net",
    "Subject": "Update on your account",
    "Date": "Mon, 25 Aug 2025 10:00:00 +0530",
}

FAKE_BODY = (
    "Update! INR 777.00 debited from HDFC Bank XX4321 on 25-AUG-25. "
    "Info: UPI-TESTSHOP-testshop@ybl. Avl bal INR 10,000.00"
)


def _cleanup():
    session = get_session()
    session.execute(delete(Transaction).where(Transaction.source_email_id == FAKE_MESSAGE_ID))
    session.execute(delete(SyncLog))
    session.commit()
    session.close()


@patch("app.ingestion.pipeline.get_plain_text_body", return_value=FAKE_BODY)
@patch("app.ingestion.pipeline.get_header")
@patch("app.ingestion.pipeline.get_message", return_value=FAKE_MESSAGE)
@patch("app.ingestion.pipeline.list_message_ids", return_value=[FAKE_MESSAGE_ID])
@patch("app.ingestion.pipeline.get_gmail_service", return_value=object())
def test_sync_inserts_then_dedupes(
    _mock_service, _mock_list_ids, _mock_get_message, mock_get_header, _mock_body
):
    mock_get_header.side_effect = lambda message, name: FAKE_HEADERS.get(name)

    try:
        first = sync(max_results=10)
        assert first["transactions_added"] == 1
        assert first["skipped_duplicate"] == 0

        second = sync(max_results=10)
        assert second["transactions_added"] == 0
        assert second["skipped_duplicate"] == 1

        session = get_session()
        row = session.query(Transaction).filter_by(source_email_id=FAKE_MESSAGE_ID).one()
        assert row.amount == 777.00
        assert row.type == "debit"
        assert row.category == "Transfer"  # raw snippet contains "UPI"
        session.close()
    finally:
        _cleanup()
