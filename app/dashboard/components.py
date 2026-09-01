from __future__ import annotations

import streamlit as st

from app.dashboard.data import last_sync_summary


def render_sync_sidebar() -> None:
    st.sidebar.header("Gmail Sync")

    summary = last_sync_summary()
    if summary:
        st.sidebar.caption(f"Last sync: {summary['last_sync_at']}")
        st.sidebar.caption(
            f"Scanned {summary['emails_scanned']} emails, "
            f"added {summary['transactions_added']} transactions"
        )
    else:
        st.sidebar.caption("No syncs yet.")

    if st.sidebar.button("Sync now", use_container_width=True):
        with st.sidebar.status("Syncing with Gmail...", expanded=True) as status:
            try:
                from app.ingestion.pipeline import sync

                result = sync(max_results=100)
                status.update(label="Sync complete", state="complete")
                st.sidebar.success(
                    f"Added {result['transactions_added']} new transactions "
                    f"({result['emails_scanned']} emails scanned, "
                    f"{result['skipped_duplicate']} duplicates skipped)."
                )
                st.rerun()
            except FileNotFoundError:
                status.update(label="Sync failed", state="error")
                st.sidebar.error(
                    "Gmail credentials not found. Complete the OAuth setup in the "
                    "README before syncing."
                )
            except Exception as exc:  # noqa: BLE001 - surface any sync error to the user
                status.update(label="Sync failed", state="error")
                st.sidebar.error(f"Sync failed: {exc}")
