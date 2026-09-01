from __future__ import annotations

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow, InstalledAppFlow
from googleapiclient.discovery import Resource, build
from sqlalchemy.orm import Session

from app.config.settings import (
    GMAIL_CLIENT_ID,
    GMAIL_CLIENT_SECRET,
    GMAIL_CREDENTIALS_PATH,
    GMAIL_SCOPES,
    GMAIL_TOKEN_PATH,
    REDIRECT_URI,
)
from app.db.models import GmailToken

# =====================================================================
# Local CLI flow: Desktop-app OAuth client, token cached to a local file.
# Used by scripts/gmail_auth_test.py and `python -m app.ingestion.pipeline`.
# Only works when the browser and the process run on the same machine.
# =====================================================================


def get_credentials() -> Credentials:
    """Load cached OAuth credentials, refreshing or running the installed-app
    login flow as needed. Never prints tokens or scopes to stdout.
    """
    creds: Credentials | None = None

    try:
        creds = Credentials.from_authorized_user_file(GMAIL_TOKEN_PATH, GMAIL_SCOPES)
    except FileNotFoundError:
        creds = None

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(GMAIL_CREDENTIALS_PATH, GMAIL_SCOPES)
        creds = flow.run_local_server(port=0)

    with open(GMAIL_TOKEN_PATH, "w") as token_file:
        token_file.write(creds.to_json())

    return creds


def get_gmail_service() -> Resource:
    creds = get_credentials()
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


# =====================================================================
# Hosted (web) flow: Web-application OAuth client, redirect through the
# deployed app's own URL, refresh token persisted in Postgres (a hosted
# app's local disk is ephemeral and resets on every restart/redeploy).
# Used by the Streamlit dashboard when running on Streamlit Community Cloud
# (or any host where the browser and the server aren't the same machine).
# =====================================================================


def build_web_flow(state: str | None = None) -> Flow:
    if not GMAIL_CLIENT_ID or not GMAIL_CLIENT_SECRET:
        raise RuntimeError(
            "GMAIL_CLIENT_ID / GMAIL_CLIENT_SECRET are not set. Add them to the "
            "app's Secrets (see README's cloud-deployment section)."
        )
    client_config = {
        "web": {
            "client_id": GMAIL_CLIENT_ID,
            "client_secret": GMAIL_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [REDIRECT_URI],
        }
    }
    return Flow.from_client_config(
        client_config, scopes=GMAIL_SCOPES, redirect_uri=REDIRECT_URI, state=state
    )


def load_credentials_from_db(session: Session) -> Credentials | None:
    row = session.query(GmailToken).first()
    if row is None:
        return None

    creds = Credentials(
        token=None,
        refresh_token=row.refresh_token,
        token_uri=row.token_uri,
        client_id=row.client_id,
        client_secret=row.client_secret,
        scopes=row.scopes.split(","),
    )
    creds.refresh(Request())
    return creds


def save_credentials_to_db(session: Session, creds: Credentials) -> None:
    row = session.query(GmailToken).first()
    if row is None:
        row = GmailToken(
            refresh_token=creds.refresh_token,
            token_uri=creds.token_uri,
            client_id=creds.client_id,
            client_secret=creds.client_secret,
            scopes=",".join(creds.scopes or GMAIL_SCOPES),
        )
        session.add(row)
    else:
        row.refresh_token = creds.refresh_token
        row.token_uri = creds.token_uri
        row.client_id = creds.client_id
        row.client_secret = creds.client_secret
        row.scopes = ",".join(creds.scopes or GMAIL_SCOPES)
    session.commit()


def clear_credentials_in_db(session: Session) -> None:
    row = session.query(GmailToken).first()
    if row is not None:
        session.delete(row)
        session.commit()


def get_gmail_service_from_db(session: Session) -> Resource:
    creds = load_credentials_from_db(session)
    if creds is None:
        raise RuntimeError("No stored Gmail credentials — connect Gmail from the sidebar first.")
    return build("gmail", "v1", credentials=creds, cache_discovery=False)
