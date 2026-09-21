"""
Google Analytics 4 integration adapter.

This module implements the OAuth *architecture* for connecting a
customer's GA4 property: building the consent URL, exchanging the
authorization code for tokens, and (once tokens exist) querying the
GA4 Data API and normalizing the response into the app's internal
shape.

It does NOT fabricate GA4 data. Until real GOOGLE_CLIENT_ID /
GOOGLE_CLIENT_SECRET / GOOGLE_REDIRECT_URI values are supplied via
environment variables, every function here reports a clear
"not configured" state instead of pretending to be connected.
"""

from urllib.parse import urlencode

import httpx

import config

AUTH_BASE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
REVOKE_URL = "https://oauth2.googleapis.com/revoke"
GA4_DATA_API_BASE = "https://analyticsdata.googleapis.com/v1beta"
GA4_SCOPE = "https://www.googleapis.com/auth/analytics.readonly"

_HTTP_TIMEOUT = 10.0


class GoogleAnalyticsAPIError(Exception):
    """
    Raised for any failure talking to Google (auth error, quota,
    network, malformed response). Callers turn this into the app's
    structured error shape rather than leaking Google's raw response
    or a stack trace to the frontend.
    """

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


def status() -> dict:
    """Honest connection state for the Data Sources page."""
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

    # Credentials exist, but no stored OAuth tokens for a workspace
    # yet in this build (token storage is part of the still-pending
    # auth/workspace persistence layer — see ROADMAP.md).
    return {
        "id": "google_analytics",
        "name": "Google Analytics 4",
        "state": "disconnected",
        "message": "Configured. Click Connect to authorize a GA4 property.",
        "property_id": config.GA4_PROPERTY_ID or None,
        "last_synced": None,
    }


def build_authorization_url(state: str) -> str:
    """
    Build the real Google OAuth 2.0 consent URL for GA4 read access.
    Raises if credentials are not configured, rather than returning
    a fake link.
    """
    if not config.google_analytics_configured():
        raise RuntimeError(
            "Google Analytics is not configured. Set GOOGLE_CLIENT_ID, "
            "GOOGLE_CLIENT_SECRET and GOOGLE_REDIRECT_URI first."
        )

    params = {
        "client_id": config.GOOGLE_CLIENT_ID,
        "redirect_uri": config.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": GA4_SCOPE,
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    return f"{AUTH_BASE_URL}?{urlencode(params)}"


def exchange_code_for_tokens(code: str) -> dict:
    """
    Real OAuth 2.0 authorization-code exchange against Google's token
    endpoint. Returns the raw token response
    (access_token, refresh_token, expires_in, scope, token_type).

    Never logs `code`, the client secret, or the returned tokens —
    callers must do the same.
    """
    payload = {
        "code": code,
        "client_id": config.GOOGLE_CLIENT_ID,
        "client_secret": config.GOOGLE_CLIENT_SECRET,
        "redirect_uri": config.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    return _post_token_request(payload)


def refresh_access_token(refresh_token: str) -> dict:
    """Exchange a stored refresh_token for a new access_token."""
    payload = {
        "refresh_token": refresh_token,
        "client_id": config.GOOGLE_CLIENT_ID,
        "client_secret": config.GOOGLE_CLIENT_SECRET,
        "grant_type": "refresh_token",
    }
    return _post_token_request(payload)


def _post_token_request(payload: dict) -> dict:
    try:
        resp = httpx.post(TOKEN_URL, data=payload, timeout=_HTTP_TIMEOUT)
    except httpx.HTTPError as exc:
        raise GoogleAnalyticsAPIError(f"Could not reach Google's token endpoint: {exc}")

    if resp.status_code != 200:
        # Google's error body is JSON like {"error": "...", "error_description": "..."}
        try:
            detail = resp.json().get("error_description") or resp.json().get("error")
        except ValueError:
            detail = resp.text[:200]
        raise GoogleAnalyticsAPIError(
            f"Google token request failed: {detail}", status_code=resp.status_code
        )

    return resp.json()


def revoke_token(token: str) -> None:
    """Best-effort revoke of an access or refresh token at Google."""
    try:
        httpx.post(
            REVOKE_URL,
            params={"token": token},
            headers={"content-type": "application/x-www-form-urlencoded"},
            timeout=_HTTP_TIMEOUT,
        )
    except httpx.HTTPError:
        # Revocation is best-effort — local disconnect must still
        # succeed even if Google can't be reached.
        pass


def run_report(access_token: str, property_id: str, metrics: list, date_ranges: list,
                dimensions: list | None = None) -> dict:
    """
    Real call to the GA4 Data API's runReport endpoint. Returns the
    normalized shape from normalize_report(), never the raw response
    passed straight to the frontend.
    """
    body = {
        "dateRanges": date_ranges,
        "metrics": [{"name": m} for m in metrics],
    }
    if dimensions:
        body["dimensions"] = [{"name": d} for d in dimensions]

    url = f"{GA4_DATA_API_BASE}/properties/{property_id}:runReport"

    try:
        resp = httpx.post(
            url,
            json=body,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=_HTTP_TIMEOUT,
        )
    except httpx.HTTPError as exc:
        raise GoogleAnalyticsAPIError(f"Could not reach the GA4 Data API: {exc}")

    if resp.status_code == 401:
        raise GoogleAnalyticsAPIError("GA4 access token expired or invalid.", status_code=401)
    if resp.status_code == 429:
        raise GoogleAnalyticsAPIError("GA4 API quota exceeded. Try again later.", status_code=429)
    if resp.status_code != 200:
        try:
            detail = resp.json().get("error", {}).get("message", resp.text[:200])
        except ValueError:
            detail = resp.text[:200]
        raise GoogleAnalyticsAPIError(f"GA4 API error: {detail}", status_code=resp.status_code)

    return normalize_report(resp.json())


def normalize_report(raw_ga4_response: dict) -> dict:
    """
    Convert a GA4 Data API runReport response into the app's internal
    NormalizedAnalyticsData shape, so the rest of the app never has to
    know about GA4-specific field names (dimensionHeaders/metricHeaders/rows).

    This is the adapter boundary described in the architecture: it is
    implemented and unit-testable now, even though it has no live data
    to normalize yet without real credentials.
    """
    dimension_headers = [h["name"] for h in raw_ga4_response.get("dimensionHeaders", [])]
    metric_headers = [h["name"] for h in raw_ga4_response.get("metricHeaders", [])]

    rows_out = []
    for row in raw_ga4_response.get("rows", []):
        dims = {
            dimension_headers[i]: v.get("value")
            for i, v in enumerate(row.get("dimensionValues", []))
        }
        mets = {
            metric_headers[i]: v.get("value")
            for i, v in enumerate(row.get("metricValues", []))
        }
        rows_out.append({"dimensions": dims, "metrics": mets})

    return {"rows": rows_out, "row_count": raw_ga4_response.get("rowCount", len(rows_out))}
