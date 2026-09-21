"""
Minimal local persistence for OAuth connections, ahead of the real
Postgres/workspace model in ROADMAP.md.

Design notes (why SQLite + a single "demo" workspace_id):
- There is no user/workspace auth yet, so there's nowhere to key
  tokens by a real user. Rather than pretend multi-tenancy exists,
  every row is stored against a fixed workspace_id="demo" — this is
  explicitly a placeholder, not a real isolation boundary. Swapping
  this for the Postgres `oauth_connections` table (per
  NEXT_INCREMENT.md section 7) is a drop-in replacement: same
  columns, same functions.
- Tokens are encrypted at rest with Fernet (symmetric, authenticated
  encryption) rather than stored as plaintext. The key comes from
  SECRET_KEY if set; otherwise a key is generated once into
  data/.token_key (0600 permissions) so at least a stolen DB file
  alone isn't enough to read tokens. This is still a stopgap, not a
  KMS — documented as such in ROADMAP.md.
"""

import base64
import hashlib
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from cryptography.fernet import Fernet, InvalidToken

import config

DEFAULT_WORKSPACE_ID = "demo"


def _fernet_key() -> bytes:
    if config.SECRET_KEY:
        digest = hashlib.sha256(config.SECRET_KEY.encode("utf-8")).digest()
        return base64.urlsafe_b64encode(digest)

    key_path = os.path.join(os.path.dirname(config.TOKEN_STORE_PATH), ".token_key")
    os.makedirs(os.path.dirname(key_path), exist_ok=True)
    if os.path.exists(key_path):
        with open(key_path, "rb") as f:
            return f.read().strip()

    key = Fernet.generate_key()
    with open(key_path, "wb") as f:
        f.write(key)
    try:
        os.chmod(key_path, 0o600)
    except OSError:
        pass
    return key


def _fernet() -> Fernet:
    return Fernet(_fernet_key())


def _encrypt(value: str | None) -> str | None:
    if value is None:
        return None
    return _fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def _decrypt(value: str | None) -> str | None:
    if value is None:
        return None
    try:
        return _fernet().decrypt(value.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        # Key changed (e.g. SECRET_KEY rotated) — treat as no usable
        # token rather than crashing the app.
        return None


@contextmanager
def _connection():
    os.makedirs(os.path.dirname(config.TOKEN_STORE_PATH), exist_ok=True)
    conn = sqlite3.connect(config.TOKEN_STORE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with _connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS oauth_connections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workspace_id TEXT NOT NULL,
                provider TEXT NOT NULL,
                property_id TEXT,
                access_token TEXT,
                refresh_token TEXT,
                token_expires_at TEXT,
                scope TEXT,
                connected_at TEXT,
                last_synced_at TEXT,
                last_error TEXT,
                UNIQUE(workspace_id, provider)
            )
            """
        )


def save_connection(provider: str, token_response: dict, property_id: str | None,
                     workspace_id: str = DEFAULT_WORKSPACE_ID):
    """
    Upsert a connection. `token_response` is the raw dict from
    Google's token endpoint (access_token, refresh_token, expires_in, scope).
    A refresh (which may omit refresh_token) preserves the previously
    stored refresh_token instead of wiping it.
    """
    init_db()
    now = datetime.now(timezone.utc).isoformat()
    expires_at = None
    if token_response.get("expires_in") is not None:
        from datetime import timedelta
        expires_at = (
            datetime.now(timezone.utc) + timedelta(seconds=int(token_response["expires_in"]))
        ).isoformat()

    with _connection() as conn:
        existing = conn.execute(
            "SELECT refresh_token FROM oauth_connections WHERE workspace_id=? AND provider=?",
            (workspace_id, provider),
        ).fetchone()

        refresh_token = token_response.get("refresh_token")
        if refresh_token is None and existing is not None:
            refresh_token = _decrypt(existing["refresh_token"])

        conn.execute(
            """
            INSERT INTO oauth_connections
                (workspace_id, provider, property_id, access_token, refresh_token,
                 token_expires_at, scope, connected_at, last_synced_at, last_error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
            ON CONFLICT(workspace_id, provider) DO UPDATE SET
                property_id=excluded.property_id,
                access_token=excluded.access_token,
                refresh_token=excluded.refresh_token,
                token_expires_at=excluded.token_expires_at,
                scope=excluded.scope,
                last_error=NULL
            """,
            (
                workspace_id, provider, property_id,
                _encrypt(token_response.get("access_token")),
                _encrypt(refresh_token),
                expires_at,
                token_response.get("scope"),
                now, None,
            ),
        )


def get_connection(provider: str, workspace_id: str = DEFAULT_WORKSPACE_ID) -> dict | None:
    init_db()
    with _connection() as conn:
        row = conn.execute(
            "SELECT * FROM oauth_connections WHERE workspace_id=? AND provider=?",
            (workspace_id, provider),
        ).fetchone()

    if row is None:
        return None

    return {
        "workspace_id": row["workspace_id"],
        "provider": row["provider"],
        "property_id": row["property_id"],
        "access_token": _decrypt(row["access_token"]),
        "refresh_token": _decrypt(row["refresh_token"]),
        "token_expires_at": row["token_expires_at"],
        "scope": row["scope"],
        "connected_at": row["connected_at"],
        "last_synced_at": row["last_synced_at"],
        "last_error": row["last_error"],
    }


def touch_synced(provider: str, workspace_id: str = DEFAULT_WORKSPACE_ID, error: str | None = None):
    init_db()
    with _connection() as conn:
        conn.execute(
            """
            UPDATE oauth_connections
            SET last_synced_at = ?, last_error = ?
            WHERE workspace_id = ? AND provider = ?
            """,
            (datetime.now(timezone.utc).isoformat(), error, workspace_id, provider),
        )


def update_access_token(provider: str, token_response: dict, workspace_id: str = DEFAULT_WORKSPACE_ID):
    """Persist a refreshed access_token without disturbing the refresh_token."""
    init_db()
    expires_at = None
    if token_response.get("expires_in") is not None:
        from datetime import timedelta
        expires_at = (
            datetime.now(timezone.utc) + timedelta(seconds=int(token_response["expires_in"]))
        ).isoformat()

    with _connection() as conn:
        conn.execute(
            """
            UPDATE oauth_connections
            SET access_token = ?, token_expires_at = ?
            WHERE workspace_id = ? AND provider = ?
            """,
            (_encrypt(token_response.get("access_token")), expires_at, workspace_id, provider),
        )


def delete_connection(provider: str, workspace_id: str = DEFAULT_WORKSPACE_ID):
    init_db()
    with _connection() as conn:
        conn.execute(
            "DELETE FROM oauth_connections WHERE workspace_id=? AND provider=?",
            (workspace_id, provider),
        )
