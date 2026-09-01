"""Step 2 smoke test: authenticate with Gmail (read-only) and print the
subject lines of the 10 most recent messages, so you can confirm OAuth
works before anything else is built on top of it.

Run: python scripts/gmail_auth_test.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Windows consoles default to a legacy codepage that can't display emoji/
# non-Latin characters often found in real email subjects — switch stdout
# to UTF-8 so those don't crash the script.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

from app.gmail_client.auth import get_gmail_service
from app.gmail_client.fetch import get_header, get_message


def main() -> None:
    service = get_gmail_service()

    response = service.users().messages().list(userId="me", maxResults=10).execute()
    message_ids = [m["id"] for m in response.get("messages", [])]

    if not message_ids:
        print("Connected, but no messages found in the inbox.")
        return

    print(f"Connected. Last {len(message_ids)} message subjects:\n")
    for msg_id in message_ids:
        message = get_message(service, msg_id)
        subject = get_header(message, "Subject") or "(no subject)"
        sender = get_header(message, "From") or "(unknown sender)"
        print(f"- {subject}  <{sender}>")


if __name__ == "__main__":
    main()
