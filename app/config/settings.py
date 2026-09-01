from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DATABASE_URL = os.environ["DATABASE_URL"]

GMAIL_CREDENTIALS_PATH = os.environ.get("GMAIL_CREDENTIALS_PATH", "./credentials.json")
GMAIL_TOKEN_PATH = os.environ.get("GMAIL_TOKEN_PATH", "./token.json")
GMAIL_SCOPES = os.environ.get(
    "GMAIL_SCOPES", "https://www.googleapis.com/auth/gmail.readonly"
).split(",")
