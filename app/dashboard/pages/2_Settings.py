from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

import pandas as pd
import streamlit as st

from app.config.filters import CATEGORY_KEYWORDS, SENDER_FILTERS, SUBJECT_KEYWORDS
from app.dashboard.components import render_sync_sidebar

st.set_page_config(page_title="Finance Dashboard - Settings", layout="wide")

render_sync_sidebar()

st.title("Settings")

st.caption(
    "Filters and category keywords live in `app/config/filters.py` so they're "
    "version-controlled and easy to review. Edit that file and restart the app "
    "to change them — this page shows the current, active configuration."
)

st.subheader("Email filters (which emails count as transaction alerts)")
st.write("**Sender addresses/domains:**")
st.write(pd.DataFrame({"sender": SENDER_FILTERS}))
st.write("**Subject keywords:**")
st.write(pd.DataFrame({"keyword": SUBJECT_KEYWORDS}))

st.subheader("Category keywords (auto-tagging rules)")
st.write(
    pd.DataFrame(
        [{"keyword": k, "category": v} for k, v in CATEGORY_KEYWORDS.items()]
    )
)

st.subheader("Add a new bank parser")
st.markdown(
    "1. Create a new file in `app/parsers/` (copy `hdfc.py` as a starting point).\n"
    "2. Write a regex matching that bank's email format.\n"
    "3. Register the parser in `app/parsers/registry.py`'s `PARSERS` list.\n"
    "4. Add the sender address to `SENDER_FILTERS` above.\n"
    "5. Add a test in `tests/test_parsers.py` with a sample email string."
)
