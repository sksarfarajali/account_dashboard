from __future__ import annotations

import re
from datetime import datetime

from app.parsers.base import BankParser, ParsedTransaction

# Example real-world text this matches:
#   "Dear Customer, Rs 850.00 has been credited to your ICICI Bank Account
#   XX5678 on 20-Aug-2025 through NEFT from ACME CORP. Avl Bal: Rs 1,20,000.00"
_PATTERN = re.compile(
    r"Rs\.?\s?(?P<amount>[\d,]+\.\d{2})\s+has\s+been\s+(?P<type>credited|debited)"
    r".*?(?:XX|X{2,})(?P<account>\d{2,6})"
    r".*?on\s+(?P<date>\d{1,2}-[A-Za-z]{3}-\d{4})"
    r"(?:.*?(?:from|to)\s+(?P<counterparty>[A-Za-z0-9 &.]+?)\.)?",
    re.IGNORECASE | re.DOTALL,
)


class IciciParser(BankParser):
    sender_match = "credit_cards@icicibank.com"

    def can_parse(self, sender: str, subject: str) -> bool:
        return self.sender_match in sender.lower() or "icicibank.com" in sender.lower()

    def parse(self, subject: str, body_text: str) -> ParsedTransaction | None:
        match = _PATTERN.search(body_text)
        if not match:
            return None

        amount = float(match.group("amount").replace(",", ""))
        txn_type = "credit" if match.group("type").lower() == "credited" else "debit"
        date = datetime.strptime(match.group("date"), "%d-%b-%Y")
        counterparty = match.group("counterparty")
        merchant = counterparty.strip() if counterparty else None

        return ParsedTransaction(
            date=date,
            type=txn_type,
            amount=amount,
            merchant=merchant,
            account_ref=match.group("account"),
            raw_snippet=body_text[:500],
        )
