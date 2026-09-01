from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def get_secret(name: str, default: str | None = None) -> str | None:
    """Look up a config value from Streamlit's secrets store first (used on
    Streamlit Community Cloud, where there is no .env file), falling back to
    environment variables / .env (used for local dev).
    """
    try:
        import streamlit as st

        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.environ.get(name, default)


_database_url = get_secret("DATABASE_URL")
if not _database_url:
    raise RuntimeError(
        "DATABASE_URL is not set. Set it in .env (local) or in the app's "
        "Secrets (Streamlit Community Cloud)."
    )
DATABASE_URL = _database_url

# --- Local CLI OAuth flow (Desktop app client, file-based token cache) ---
GMAIL_CREDENTIALS_PATH = get_secret("GMAIL_CREDENTIALS_PATH", "./credentials.json")
GMAIL_TOKEN_PATH = get_secret("GMAIL_TOKEN_PATH", "./token.json")

GMAIL_SCOPES = get_secret(
    "GMAIL_SCOPES", "https://www.googleapis.com/auth/gmail.readonly"
).split(",")

# --- Hosted web OAuth flow (Web application client, token stored in DB) ---
GMAIL_CLIENT_ID = get_secret("GMAIL_CLIENT_ID")
GMAIL_CLIENT_SECRET = get_secret("GMAIL_CLIENT_SECRET")
REDIRECT_URI = get_secret("REDIRECT_URI", "http://localhost:8501")
