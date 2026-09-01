from __future__ import annotations

import re
from datetime import datetime

from app.parsers.base import BankParser, ParsedTransaction

# Example real-world text this matches:
#   "Axis Bank Alert: INR 320.50 spent on your Credit Card XX9012 at AMAZON
#   on 18-08-2025 12:30:45"
_PATTERN = re.compile(
    r"INR\s?(?P<amount>[\d,]+\.\d{2})\s+spent\s+on\s+your\s+Credit\s+Card\s+"
    r"(?:XX|X{2,})(?P<account>\d{2,6})\s+at\s+(?P<merchant>[A-Za-z0-9 &.]+?)\s+"
    r"on\s+(?P<date>\d{1,2}-\d{1,2}-\d{4})",
    re.IGNORECASE | re.DOTALL,
)


class AxisParser(BankParser):
    sender_match = "alerts@axisbank.com"

    def can_parse(self, sender: str, subject: str) -> bool:
        return self.sender_match in sender.lower()

    def parse(self, subject: str, body_text: str) -> ParsedTransaction | None:
        match = _PATTERN.search(body_text)
        if not match:
            return None

        amount = float(match.group("amount").replace(",", ""))
        date = datetime.strptime(match.group("date"), "%d-%m-%Y")

        # Axis credit-card alerts are always spends (debits) in this format.
        return ParsedTransaction(
            date=date,
            type="debit",
            amount=amount,
            merchant=match.group("merchant").strip(),
            account_ref=match.group("account"),
            raw_snippet=body_text[:500],
        )
