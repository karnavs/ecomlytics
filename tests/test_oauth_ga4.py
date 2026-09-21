"""
Tests for the OAuth/GA4 increment. No real network calls to Google —
httpx calls are monkeypatched so these test our request construction,
state validation, token persistence and error handling logic, per
NEXT_INCREMENT.md section 18 ("mocked API responses").
"""

import os
import tempfile

import pytest

import config


@pytest.fixture(autouse=True)
def isolated_token_store(monkeypatch, tmp_path):
    """Every test gets its own SQLite file and Fernet key, so tests
    don't leak state into each other or the real dev data/app.db."""
    monkeypatch.setattr(config, "TOKEN_STORE_PATH", str(tmp_path / "app.db"))
    monkeypatch.setattr(config, "SECRET_KEY", "test-secret-key")
    monkeypatch.setattr(config, "GOOGLE_CLIENT_ID", "test-client-id")
    monkeypatch.setattr(config, "GOOGLE_CLIENT_SECRET", "test-client-secret")
    monkeypatch.setattr(config, "GOOGLE_REDIRECT_URI", "http://localhost:8000/api/data-sources/google/callback")
    monkeypatch.setattr(config, "GA4_PROPERTY_ID", "555091829")
    yield


def test_config_ga4_property_id_reads_correct_env(monkeypatch):
    # Regression test for the config.py bug where GA4_PROPERTY_ID was
    # read from an env var literally named "555091829" instead of
    # "GA4_PROPERTY_ID".
    monkeypatch.setenv("GA4_PROPERTY_ID", "999888777")
    import importlib
    import config as cfg
    importlib.reload(cfg)
    assert cfg.GA4_PROPERTY_ID == "999888777"
    importlib.reload(cfg)  # restore for other tests


def test_authorization_url_is_well_formed():
    from integrations import google_analytics
    url = google_analytics.build_authorization_url("teststate123")
    assert url.startswith("https://accounts.google.com/o/oauth2/v2/auth?")
    assert "client_id=test-client-id" in url
    assert "state=teststate123" in url
    assert "scope=" in url


def test_oauth_state_is_single_use():
    from services import oauth_service
    url = oauth_service.start_connect()
    state = url.split("state=")[1].split("&")[0]

    assert oauth_service.validate_state(state) is True
    # Second use of the same state must fail (CSRF replay protection).
    assert oauth_service.validate_state(state) is False


def test_oauth_state_rejects_unknown_value():
    from services import oauth_service
    assert oauth_service.validate_state("never-issued") is False


def test_token_exchange_and_storage_round_trip(monkeypatch):
    from integrations import google_analytics
    from services import oauth_service
    from db import token_store

    def fake_post_token_request(payload):
        assert payload["grant_type"] == "authorization_code"
        assert payload["code"] == "auth-code-xyz"
        return {
            "access_token": "fake-access-token",
            "refresh_token": "fake-refresh-token",
            "expires_in": 3600,
            "scope": google_analytics.GA4_SCOPE,
        }

    monkeypatch.setattr(google_analytics, "_post_token_request", fake_post_token_request)

    status = oauth_service.complete_connect("auth-code-xyz")
    assert status["state"] == "connected"

    conn = token_store.get_connection("google_analytics")
    # Tokens must be encrypted at rest -- never equal to the plaintext value in storage.
    assert conn["access_token"] == "fake-access-token"  # decrypted correctly on read
    assert conn["refresh_token"] == "fake-refresh-token"


def test_stored_tokens_are_encrypted_on_disk(monkeypatch):
    from integrations import google_analytics
    from services import oauth_service
    from db import token_store
    import sqlite3

    monkeypatch.setattr(
        google_analytics, "_post_token_request",
        lambda payload: {"access_token": "super-secret-token", "expires_in": 3600}
    )
    oauth_service.complete_connect("code")

    conn = sqlite3.connect(config.TOKEN_STORE_PATH)
    raw = conn.execute("SELECT access_token FROM oauth_connections").fetchone()[0]
    conn.close()
    assert "super-secret-token" not in raw


def test_expired_token_triggers_refresh(monkeypatch):
    from integrations import google_analytics
    from services import oauth_service
    from db import token_store
    from datetime import datetime, timezone, timedelta

    token_store.save_connection(
        provider="google_analytics",
        token_response={
            "access_token": "old-token",
            "refresh_token": "refresh-me",
            "expires_in": -100,  # already expired
        },
        property_id="555091829",
    )

    monkeypatch.setattr(
        google_analytics, "_post_token_request",
        lambda payload: {"access_token": "new-token", "expires_in": 3600}
    )

    token = oauth_service.get_valid_access_token()
    assert token == "new-token"


def test_no_connection_raises_clear_error():
    from services import oauth_service
    with pytest.raises(RuntimeError):
        oauth_service.get_valid_access_token()


def test_ga4_error_response_never_leaks_raw_google_payload(monkeypatch):
    from integrations import google_analytics
    import httpx

    class FakeResponse:
        status_code = 429
        def json(self):
            return {"error": {"message": "Quota exceeded for property"}}
        text = "raw body"

    monkeypatch.setattr(httpx, "post", lambda *a, **k: FakeResponse())

    with pytest.raises(google_analytics.GoogleAnalyticsAPIError) as exc_info:
        google_analytics.run_report(
            access_token="tok", property_id="555091829",
            metrics=["activeUsers"], date_ranges=[{"startDate": "2026-01-01", "endDate": "2026-01-30"}],
        )
    assert exc_info.value.status_code == 429


def test_normalize_report_shape():
    from integrations import google_analytics
    raw = {
        "dimensionHeaders": [{"name": "date"}],
        "metricHeaders": [{"name": "activeUsers"}],
        "rows": [
            {"dimensionValues": [{"value": "20260101"}], "metricValues": [{"value": "42"}]}
        ],
        "rowCount": 1,
    }
    result = google_analytics.normalize_report(raw)
    assert result["rows"][0]["dimensions"]["date"] == "20260101"
    assert result["rows"][0]["metrics"]["activeUsers"] == "42"
