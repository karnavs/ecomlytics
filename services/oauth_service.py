"""
Orchestrates the Google OAuth connect/callback/refresh/disconnect
flow: CSRF state, token exchange, persistence (via db.token_store),
and token refresh. integrations.google_analytics stays the "dumb"
HTTP client; this module is the business logic on top of it.
"""

import secrets
import time

from integrations import google_analytics
from db import token_store

PROVIDER = "google_analytics"

# In-memory CSRF state store: {state: expires_at_epoch}.
# Good enough for a single local dev process; a real deployment with
# multiple workers/restarts needs this in Redis/DB instead — noted
# in ROADMAP.md.
_STATE_TTL_SECONDS = 600
_pending_states: dict[str, float] = {}


def start_connect() -> str:
    """Generate a CSRF state, remember it, and return the Google consent URL."""
    state = secrets.token_urlsafe(24)
    _pending_states[state] = time.time() + _STATE_TTL_SECONDS
    _prune_expired_states()
    return google_analytics.build_authorization_url(state)


def _prune_expired_states():
    now = time.time()
    expired = [s for s, exp in _pending_states.items() if exp < now]
    for s in expired:
        _pending_states.pop(s, None)


def validate_state(state: str | None) -> bool:
    """
    Consume and validate a returned OAuth `state`. Single-use: once
    checked (pass or fail) it's removed, so a replayed callback can't
    reuse it.
    """
    if not state:
        return False
    expires_at = _pending_states.pop(state, None)
    if expires_at is None:
        return False
    return expires_at >= time.time()


def complete_connect(code: str) -> dict:
    """
    Exchange the authorization code for tokens and persist them.
    Returns the connection status dict for the frontend.
    """
    token_response = google_analytics.exchange_code_for_tokens(code)
    token_store.save_connection(
        provider=PROVIDER,
        token_response=token_response,
        property_id=_property_id_for_new_connection(),
    )
    return status()


def _property_id_for_new_connection() -> str | None:
    import config
    return config.GA4_PROPERTY_ID or None


def get_valid_access_token() -> str:
    """
    Return a usable access token, refreshing it first if it's expired
    or close to expiring. Raises RuntimeError with a clear message if
    there's no connection or no refresh token to recover with.
    """
    from datetime import datetime, timezone

    conn = token_store.get_connection(PROVIDER)
    if conn is None or not conn.get("access_token"):
        raise RuntimeError("Google Analytics is not connected.")

    needs_refresh = True
    if conn.get("token_expires_at"):
        expires_at = datetime.fromisoformat(conn["token_expires_at"])
        needs_refresh = expires_at <= datetime.now(timezone.utc)

    if not needs_refresh:
        return conn["access_token"]

    if not conn.get("refresh_token"):
        raise RuntimeError(
            "The stored Google Analytics access token expired and no "
            "refresh token is available. Please reconnect."
        )

    refreshed = google_analytics.refresh_access_token(conn["refresh_token"])
    token_store.update_access_token(PROVIDER, refreshed)
    return refreshed["access_token"]


def disconnect():
    conn = token_store.get_connection(PROVIDER)
    if conn and conn.get("refresh_token"):
        google_analytics.revoke_token(conn["refresh_token"])
    elif conn and conn.get("access_token"):
        google_analytics.revoke_token(conn["access_token"])
    token_store.delete_connection(PROVIDER)


def status() -> dict:
    """Honest connection state, now aware of stored tokens."""
    import config

    if not config.google_analytics_configured():
        return {
            "id": "google_analytics",
            "name": "Google Analytics 4",
            "state": "not_configured",
            "message": (
                "Set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET and "
                "GOOGLE_REDIRECT_URI to enable this integration."
            ),
            "property_id": None,
            "last_synced": None,
        }

    conn = token_store.get_connection(PROVIDER)
    if conn is None:
        return {
            "id": "google_analytics",
            "name": "Google Analytics 4",
            "state": "disconnected",
            "message": "Configured. Click Connect to authorize a GA4 property.",
            "property_id": config.GA4_PROPERTY_ID or None,
            "last_synced": None,
        }

    if conn.get("last_error"):
        return {
            "id": "google_analytics",
            "name": "Google Analytics 4",
            "state": "needs_attention",
            "message": conn["last_error"],
            "property_id": conn.get("property_id"),
            "last_synced": conn.get("last_synced_at"),
        }

    return {
        "id": "google_analytics",
        "name": "Google Analytics 4",
        "state": "connected",
        "message": "Connected.",
        "property_id": conn.get("property_id"),
        "last_synced": conn.get("last_synced_at"),
    }
