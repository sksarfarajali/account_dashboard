from __future__ import annotations

import re
from datetime import datetime

from app.parsers.base import BankParser, ParsedTransaction

# Example real-world text this matches:
#   "Update! INR 1,250.00 debited from HDFC Bank XX1234 on 25-AUG-25.
#   Info: UPI-SWIGGY-swiggy@ybl. Avl bal INR 45,000.00"
_PATTERN = re.compile(
    r"INR\s?(?P<amount>[\d,]+\.\d{2})\s+(?P<type>debited|credited)"
    r".*?(?:XX|X{2,})(?P<account>\d{2,6})"
    r".*?on\s+(?P<date>\d{1,2}-[A-Za-z]{3}-\d{2,4})"
    r"(?:.*?Info:\s*(?P<info>[^.\n]+))?",
    re.IGNORECASE | re.DOTALL,
)


class HdfcParser(BankParser):
    sender_match = "alerts@hdfcbank.net"

    def can_parse(self, sender: str, subject: str) -> bool:
        return self.sender_match in sender.lower()

    def parse(self, subject: str, body_text: str) -> ParsedTransaction | None:
        match = _PATTERN.search(body_text)
        if not match:
            return None

        amount = float(match.group("amount").replace(",", ""))
        txn_type = "debit" if match.group("type").lower() == "debited" else "credit"
        date = datetime.strptime(match.group("date"), "%d-%b-%y")
        info = match.group("info")
        merchant = info.strip() if info else None

        return ParsedTransaction(
            date=date,
            type=txn_type,
            amount=amount,
            merchant=merchant,
            account_ref=match.group("account"),
            raw_snippet=body_text[:500],
        )
