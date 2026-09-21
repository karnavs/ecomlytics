"""
Fetches real GA4 metrics for the connected property and normalizes
them into the app's overview shape, tagged with source="ga4" so the
frontend can never confuse this with demo data.
"""

from datetime import date, timedelta

from integrations import google_analytics
from integrations.google_analytics import GoogleAnalyticsAPIError
from db import token_store
from services import oauth_service


OVERVIEW_METRICS = [
    "activeUsers",
    "newUsers",
    "sessions",
    "engagedSessions",
    "engagementRate",
    "eventCount",
]


def fetch_overview(days: int = 30) -> dict:
    """
    Real GA4 runReport call for the connected property. Raises
    RuntimeError (not-connected) or GoogleAnalyticsAPIError
    (request/auth/quota failure) rather than returning fake numbers —
    callers turn these into the app's structured error shape.
    """
    conn = token_store.get_connection(oauth_service.PROVIDER)
    if conn is None or not conn.get("property_id"):
        raise RuntimeError("Google Analytics is not connected.")

    access_token = oauth_service.get_valid_access_token()

    end = date.today()
    start = end - timedelta(days=days - 1)

    try:
        normalized = google_analytics.run_report(
            access_token=access_token,
            property_id=conn["property_id"],
            metrics=OVERVIEW_METRICS,
            date_ranges=[{"startDate": str(start), "endDate": str(end)}],
        )
    except GoogleAnalyticsAPIError as exc:
        token_store.touch_synced(oauth_service.PROVIDER, error=str(exc))
        raise

    token_store.touch_synced(oauth_service.PROVIDER)

    values = {}
    if normalized["rows"]:
        row_metrics = normalized["rows"][0]["metrics"]
        for name in OVERVIEW_METRICS:
            raw = row_metrics.get(name)
            values[name] = _coerce_number(raw)
    else:
        values = {name: None for name in OVERVIEW_METRICS}

    return {
        "source": "ga4",
        "property_id": conn["property_id"],
        "date_range": {"start": str(start), "end": str(end)},
        "metrics": values,
    }


def _coerce_number(raw):
    if raw is None:
        return None
    try:
        if "." in raw:
            return round(float(raw), 4)
        return int(raw)
    except (TypeError, ValueError):
        return raw
