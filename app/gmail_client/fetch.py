from __future__ import annotations

from typing import Any

from googleapiclient.discovery import Resource

from app.config.filters import build_gmail_query


def list_message_ids(
    service: Resource, query: str | None = None, max_results: int = 10
) -> list[str]:
    """Return Gmail message IDs matching `query` (defaults to the configured
    transaction-alert filters), newest first, up to `max_results`.
    """
    query = query if query is not None else build_gmail_query()
    ids: list[str] = []
    request = service.users().messages().list(userId="me", q=query, maxResults=min(max_results, 500))

    while request is not None and len(ids) < max_results:
        response = request.execute()
        ids.extend(m["id"] for m in response.get("messages", []))
        request = service.users().messages().list_next(request, response)

    return ids[:max_results]


def get_message(service: Resource, message_id: str) -> dict[str, Any]:
    return service.users().messages().get(userId="me", id=message_id, format="full").execute()


def get_header(message: dict[str, Any], name: str) -> str | None:
    headers = message.get("payload", {}).get("headers", [])
    for h in headers:
        if h.get("name", "").lower() == name.lower():
            return h.get("value")
    return None


def get_plain_text_body(message: dict[str, Any]) -> str:
    """Extract the best-effort plain-text body from a Gmail message payload,
    walking multipart structures and decoding base64url.
    """
    import base64

    def walk(part: dict[str, Any]) -> str | None:
        mime_type = part.get("mimeType", "")
        body_data = part.get("body", {}).get("data")
        if mime_type == "text/plain" and body_data:
            return base64.urlsafe_b64decode(body_data).decode("utf-8", errors="replace")
        for sub in part.get("parts", []) or []:
            result = walk(sub)
            if result:
                return result
        # fall back to html if no plain text found at this level
        if mime_type == "text/html" and body_data:
            return base64.urlsafe_b64decode(body_data).decode("utf-8", errors="replace")
        return None

    payload = message.get("payload", {})
    return walk(payload) or ""
