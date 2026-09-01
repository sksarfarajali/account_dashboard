from __future__ import annotations

from app.config.filters import CATEGORY_KEYWORDS, DEFAULT_CATEGORY


def categorize(merchant: str | None, raw_snippet: str) -> str:
    text = f"{merchant or ''} {raw_snippet}".lower()
    for keyword, category in CATEGORY_KEYWORDS.items():
        if keyword in text:
            return category
    return DEFAULT_CATEGORY
