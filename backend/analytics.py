"""Anonymous, privacy-preserving usage analytics backed by Supabase.

No personal data, IP addresses, or session-identifying information is ever
recorded. Only aggregate, anonymised facts are written: search counts,
searched product names, platforms viewed, and a random per-browser session
token (stored client-side, never linked to identity).

If SUPABASE_URL / SUPABASE_KEY are not configured, analytics calls become
no-ops so the app still runs fully without an analytics backend.
"""
import os

import requests

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

_ENABLED = bool(SUPABASE_URL and SUPABASE_KEY)

_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal",
}


def _insert(table: str, row: dict):
    if not _ENABLED:
        return
    try:
        requests.post(
            f"{SUPABASE_URL}/rest/v1/{table}",
            headers=_HEADERS,
            json=row,
            timeout=4,
        )
    except requests.RequestException:
        pass


def record_search(product_query: str, session_id: str):
    """Log an anonymised search event (table: search_events)."""
    _insert("search_events", {
        "product_query": product_query[:200],
        "session_id": session_id,
    })


def record_platform_view(platform: str, session_id: str):
    """Log that a platform's results were viewed (table: platform_views)."""
    _insert("platform_views", {
        "platform": platform,
        "session_id": session_id,
    })


def is_enabled() -> bool:
    return _ENABLED
