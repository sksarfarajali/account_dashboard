from __future__ import annotations

import re
from datetime import datetime

from app.parsers.base import BankParser, ParsedTransaction

# Best-effort fallback for banks without a dedicated parser yet: looks for
# any "Rs./INR <amount> ... debited/credited" pattern. No date extraction —
# falls back to the email's own received date, filled in by the ingestion
# pipeline, not here.
_AMOUNT_TYPE_PATTERN = re.compile(
    r"(?:Rs\.?|INR)\s?(?P<amount>[\d,]+\.\d{2}).{0,40}?(?P<type>debited|credited|spent)",
    re.IGNORECASE | re.DOTALL,
)


class GenericParser(BankParser):
    sender_match = "*"

    def can_parse(self, sender: str, subject: str) -> bool:
        return True  # last-resort fallback, always eligible

    def parse(self, subject: str, body_text: str) -> ParsedTransaction | None:
        match = _AMOUNT_TYPE_PATTERN.search(body_text)
        if not match:
            return None

        amount = float(match.group("amount").replace(",", ""))
        raw_type = match.group("type").lower()
        txn_type = "credit" if raw_type == "credited" else "debit"

        return ParsedTransaction(
            date=datetime.now(),  # overwritten by ingestion with the email's date header
            type=txn_type,
            amount=amount,
            merchant=None,
            account_ref=None,
            raw_snippet=body_text[:500],
        )
