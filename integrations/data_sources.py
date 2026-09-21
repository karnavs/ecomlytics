"""
Aggregates the state of every data source so the Data Sources page
shows the truth: what's actually connected vs. what needs setup.
"""

from datetime import datetime
from pathlib import Path

from services import oauth_service

BASE = Path(__file__).resolve().parents[1]
DATA_DIR = BASE / "data"


def _csv_source() -> dict:
    files = ["orders.csv", "customers.csv", "products.csv"]
    existing = [f for f in files if (DATA_DIR / f).exists()]
    if not existing:
        return {
            "id": "demo_csv",
            "name": "Demo Data (CSV)",
            "state": "disconnected",
            "message": "No demo dataset found in /data.",
            "last_synced": None,
        }

    newest_mtime = max((DATA_DIR / f).stat().st_mtime for f in existing)
    return {
        "id": "demo_csv",
        "name": "Demo Data (CSV)",
        "state": "connected",
        "message": f"{len(existing)}/{len(files)} demo files loaded.",
        "last_synced": datetime.fromtimestamp(newest_mtime).isoformat(),
    }


def list_data_sources() -> list:
    return [
        _csv_source(),
        oauth_service.status(),
    ]
