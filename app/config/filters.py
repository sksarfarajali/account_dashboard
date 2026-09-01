"""Configurable rules for which emails count as transaction alerts, and how
transactions get auto-categorized. Edit these lists as you add banks/cards —
no other code should need to change.
"""

from __future__ import annotations

# Gmail search is OR'd across these sender domains/addresses.
SENDER_FILTERS: list[str] = [
    "alerts@hdfcbank.net",
    "credit_cards@icicibank.com",
    "alerts@axisbank.com",
]

# Gmail search is OR'd across these subject-line substrings, in addition to
# SENDER_FILTERS (a message matches if sender OR subject matches).
SUBJECT_KEYWORDS: list[str] = [
    "debited",
    "credited",
    "transaction alert",
    "payment successful",
    "spent on your card",
]

# Keyword -> category. Matched case-insensitively against the parsed
# merchant/description text. First match wins; falls back to "Other".
CATEGORY_KEYWORDS: dict[str, str] = {
    "swiggy": "Food",
    "zomato": "Food",
    "restaurant": "Food",
    "cafe": "Food",
    "amazon": "Shopping",
    "flipkart": "Shopping",
    "myntra": "Shopping",
    "electricity": "Bills",
    "broadband": "Bills",
    "recharge": "Bills",
    "insurance": "Bills",
    "salary": "Salary",
    "neft": "Transfer",
    "imps": "Transfer",
    "upi": "Transfer",
}

DEFAULT_CATEGORY = "Other"


def build_gmail_query() -> str:
    """Combine sender + subject filters into a single Gmail search query."""
    sender_clause = " OR ".join(f"from:{s}" for s in SENDER_FILTERS)
    subject_clause = " OR ".join(f'subject:"{s}"' for s in SUBJECT_KEYWORDS)
    parts = [p for p in (sender_clause, subject_clause) if p]
    return " OR ".join(f"({p})" for p in parts)
