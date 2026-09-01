from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ParsedTransaction:
    date: datetime
    type: str  # "debit" | "credit"
    amount: float
    merchant: str | None
    account_ref: str | None
    raw_snippet: str

    def dedupe_key(self, source_email_id: str) -> str:
        raw = f"{source_email_id}|{self.amount}|{self.date.isoformat()}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class BankParser(ABC):
    """One subclass per bank/sender. Add a new bank by adding a new file in
    this package and registering it in `registry.py` — nothing else changes.
    """

    #: sender address/domain this parser is responsible for (used for routing)
    sender_match: str

    @abstractmethod
    def can_parse(self, sender: str, subject: str) -> bool:
        ...

    @abstractmethod
    def parse(self, subject: str, body_text: str) -> ParsedTransaction | None:
        """Return a ParsedTransaction, or None if the email doesn't actually
        contain a transaction (e.g. a promo email that matched the filter).
        """
        ...
