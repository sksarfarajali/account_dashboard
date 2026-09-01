from __future__ import annotations

import streamlit as st

from app.config.settings import GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET
from app.dashboard.data import last_sync_summary
from app.db.session import get_session
from app.gmail_client.auth import (
    build_web_flow,
    clear_credentials_in_db,
    get_gmail_service_from_db,
    load_credentials_from_db,
    save_credentials_to_db,
)

# Whether GMAIL_CLIENT_ID/SECRET (a "Web application" OAuth client) are
# configured decides which flow the sidebar uses:
#   - configured   -> hosted flow: browser redirect through Google, token in DB
#                      (works when the browser and the server are different
#                      machines, e.g. Streamlit Community Cloud)
#   - not configured -> local flow: the same one scripts/gmail_auth_test.py
#                      uses (credentials.json + token.json on disk) — this is
#                      the default for running the app on your own machine.
_WEB_OAUTH_CONFIGURED = bool(GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET)


def render_sync_sidebar() -> None:
    st.sidebar.header("Gmail Sync")

    if _WEB_OAUTH_CONFIGURED:
        _render_hosted_flow()
    else:
        _render_local_flow()


def _render_sync_now(service_getter) -> None:
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

                result = sync(max_results=100, service=service_getter())
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


# --- Local flow (default): credentials.json + token.json on disk ---------


def _render_local_flow() -> None:
    def _get_service():
        from app.gmail_client.auth import get_gmail_service

        return get_gmail_service()

    st.sidebar.caption("Using local OAuth (credentials.json on disk).")
    _render_sync_now(_get_service)


# --- Hosted flow: browser redirect through Google, token stored in DB ----


def _complete_oauth_if_redirected() -> None:
    params = st.query_params
    if "code" not in params:
        return

    session = get_session()
    try:
        flow = build_web_flow(state=params.get("state"))
        flow.fetch_token(code=params["code"])
        save_credentials_to_db(session, flow.credentials)
    except Exception as exc:  # noqa: BLE001 - surface OAuth errors to the user
        st.sidebar.error(f"Gmail connection failed: {exc}")
    finally:
        session.close()

    st.query_params.clear()
    st.rerun()


def _render_hosted_flow() -> None:
    _complete_oauth_if_redirected()

    session = get_session()
    try:
        creds = load_credentials_from_db(session)
    except Exception:
        creds = None
    session.close()

    if creds is None:
        st.sidebar.warning("Gmail not connected.")
        flow = build_web_flow()
        auth_url, _state = flow.authorization_url(
            access_type="offline", include_granted_scopes="true", prompt="consent"
        )
        st.sidebar.link_button("Connect Gmail", auth_url, use_container_width=True)
        return

    st.sidebar.success("Gmail connected.")
    if st.sidebar.button("Disconnect", use_container_width=True):
        session = get_session()
        clear_credentials_in_db(session)
        session.close()
        st.rerun()

    def _get_service():
        session = get_session()
        try:
            return get_gmail_service_from_db(session)
        finally:
            session.close()

    _render_sync_now(_get_service)
