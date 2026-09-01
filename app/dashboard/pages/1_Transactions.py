from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

import streamlit as st

from app.config.filters import CATEGORY_KEYWORDS, DEFAULT_CATEGORY
from app.dashboard.components import render_sync_sidebar
from app.dashboard.data import load_transactions, update_category

st.set_page_config(page_title="Finance Dashboard - Transactions", layout="wide")

render_sync_sidebar()

st.title("Transactions")

df = load_transactions()

if df.empty:
    st.info("No transactions yet. Run a sync from the sidebar to get started.")
    st.stop()

search = st.text_input("Search merchant / snippet")
categories = sorted(set(CATEGORY_KEYWORDS.values()) | {DEFAULT_CATEGORY})
category_filter = st.multiselect("Category", categories, default=[])
type_filter = st.multiselect("Type", ["debit", "credit"], default=[])

filtered = df.copy()
if search:
    mask = filtered["merchant"].fillna("").str.contains(search, case=False) | filtered[
        "raw_snippet"
    ].fillna("").str.contains(search, case=False)
    filtered = filtered[mask]
if category_filter:
    filtered = filtered[filtered["category"].isin(category_filter)]
if type_filter:
    filtered = filtered[filtered["type"].isin(type_filter)]

st.caption(f"{len(filtered)} of {len(df)} transactions")

sort_col = st.selectbox("Sort by", ["date", "amount", "merchant", "category"])
sort_desc = st.checkbox("Descending", value=True)
filtered = filtered.sort_values(sort_col, ascending=not sort_desc)

st.dataframe(
    filtered[["date", "type", "amount", "merchant", "category", "account_ref"]],
    use_container_width=True,
    hide_index=True,
)

st.subheader("Override a transaction's category")
if not filtered.empty:
    options = {
        f"#{row.id} — {row.date.date()} — ₹{row.amount:,.2f} — {row.merchant or '(no merchant)'}": row.id
        for row in filtered.itertuples()
    }
    selected_label = st.selectbox("Transaction", list(options.keys()))
    new_category = st.selectbox("New category", categories, key="override_category")
    if st.button("Apply category"):
        update_category(options[selected_label], new_category)
        st.success("Category updated.")
        st.rerun()
