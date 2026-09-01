from __future__ import annotations

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build

from app.config.settings import GMAIL_CREDENTIALS_PATH, GMAIL_SCOPES, GMAIL_TOKEN_PATH


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
