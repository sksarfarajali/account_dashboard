from __future__ import annotations

from app.parsers.axis import AxisParser
from app.parsers.base import BankParser, ParsedTransaction
from app.parsers.generic import GenericParser
from app.parsers.hdfc import HdfcParser
from app.parsers.icici import IciciParser

# Order matters: specific bank parsers are tried before the generic fallback.
PARSERS: list[BankParser] = [
    HdfcParser(),
    IciciParser(),
    AxisParser(),
    GenericParser(),
]


def parse_email(sender: str, subject: str, body_text: str) -> ParsedTransaction | None:
    for parser in PARSERS:
        if parser.can_parse(sender, subject):
            result = parser.parse(subject, body_text)
            if result is not None:
                return result
    return None
