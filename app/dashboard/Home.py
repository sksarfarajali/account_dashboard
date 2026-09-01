from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pandas as pd
import plotly.express as px
import streamlit as st

from app.dashboard.components import render_sync_sidebar
from app.dashboard.data import load_transactions

st.set_page_config(page_title="Finance Dashboard - Overview", layout="wide")

render_sync_sidebar()

st.title("Overview")

RANGE_OPTIONS = {
    "This month": "this_month",
    "Last 30 days": "last_30",
    "Custom range": "custom",
}
choice = st.selectbox("Date range", list(RANGE_OPTIONS.keys()))

today = dt.date.today()
if RANGE_OPTIONS[choice] == "this_month":
    start = today.replace(day=1)
    end = today
elif RANGE_OPTIONS[choice] == "last_30":
    start = today - dt.timedelta(days=30)
    end = today
else:
    col1, col2 = st.columns(2)
    start = col1.date_input("Start date", today - dt.timedelta(days=30))
    end = col2.date_input("End date", today)

df = load_transactions(start=start, end=end)

if df.empty:
    st.info("No transactions in this range yet. Run a sync from the sidebar to get started.")
    st.stop()

credits = df.loc[df["type"] == "credit", "amount"].sum()
debits = df.loc[df["type"] == "debit", "amount"].sum()
net = credits - debits

col1, col2, col3 = st.columns(3)
col1.metric("Total credits", f"₹{credits:,.2f}")
col2.metric("Total debits", f"₹{debits:,.2f}")
col3.metric("Net change", f"₹{net:,.2f}")

st.subheader("Daily spend vs income")
daily = (
    df.assign(day=df["date"].dt.date)
    .groupby(["day", "type"])["amount"]
    .sum()
    .reset_index()
)
fig_daily = px.bar(daily, x="day", y="amount", color="type", barmode="group")
st.plotly_chart(fig_daily, use_container_width=True)

st.subheader("Spend by category")
spend_by_category = (
    df.loc[df["type"] == "debit"].groupby("category")["amount"].sum().reset_index()
)
if not spend_by_category.empty:
    fig_category = px.pie(spend_by_category, names="category", values="amount")
    st.plotly_chart(fig_category, use_container_width=True)
else:
    st.caption("No debit transactions in this range.")
