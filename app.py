from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from analytics.metrics import (
    overview,
    product_metrics,
    customer_segments,
    funnel,
)

from insights.engine import generate_insights

from integrations.data_sources import list_data_sources
from integrations.google_analytics import GoogleAnalyticsAPIError
from services import oauth_service, ga4_service
from fastapi import HTTPException


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"
PAGES_DIR = FRONTEND_DIR / "pages"


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="Ecomlytics API",
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# CHECK FRONTEND DIRECTORIES
# ============================================================

if not FRONTEND_DIR.exists():
    raise RuntimeError(
        f"Frontend directory not found: {FRONTEND_DIR}"
    )

if not PAGES_DIR.exists():
    raise RuntimeError(
        f"Frontend pages directory not found: {PAGES_DIR}"
    )


# ============================================================
# ROOT
# ============================================================

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(
        url="/login.html",
        status_code=307,
    )


# ============================================================
# FRONTEND - MAIN PAGES
# ============================================================

@app.get("/login.html", include_in_schema=False)
def login_page():
    return FileResponse(
        FRONTEND_DIR / "login.html"
    )


@app.get("/index.html", include_in_schema=False)
def index_page():
    return FileResponse(
        FRONTEND_DIR / "index.html"
    )


# ============================================================
# FRONTEND - CORRECT PAGE PATHS
# ============================================================

@app.get("/pages/sales.html", include_in_schema=False)
def sales_page():
    return FileResponse(
        PAGES_DIR / "sales.html"
    )


@app.get("/pages/products.html", include_in_schema=False)
def products_page():
    return FileResponse(
        PAGES_DIR / "products.html"
    )


@app.get("/pages/customers.html", include_in_schema=False)
def customers_page():
    return FileResponse(
        PAGES_DIR / "customers.html"
    )


@app.get("/pages/retention.html", include_in_schema=False)
def retention_page():
    return FileResponse(
        PAGES_DIR / "retention.html"
    )


@app.get("/pages/insights.html", include_in_schema=False)
def insights_page():
    return FileResponse(
        PAGES_DIR / "insights.html"
    )


# ============================================================
# FRONTEND - OLD PATH COMPATIBILITY
# ============================================================
#
# These routes prevent 404 errors if an older app.js is still
# using /sales.html instead of /pages/sales.html.
#
# They redirect automatically to the correct location.
# ============================================================

@app.get("/sales.html", include_in_schema=False)
def old_sales_page():
    return RedirectResponse(
        url="/pages/sales.html",
        status_code=307,
    )


@app.get("/products.html", include_in_schema=False)
def old_products_page():
    return RedirectResponse(
        url="/pages/products.html",
        status_code=307,
    )


@app.get("/customers.html", include_in_schema=False)
def old_customers_page():
    return RedirectResponse(
        url="/pages/customers.html",
        status_code=307,
    )


@app.get("/retention.html", include_in_schema=False)
def old_retention_page():
    return RedirectResponse(
        url="/pages/retention.html",
        status_code=307,
    )


@app.get("/insights.html", include_in_schema=False)
def old_insights_page():
    return RedirectResponse(
        url="/pages/insights.html",
        status_code=307,
    )


# ============================================================
# API ROUTES
# ============================================================

@app.get("/api/overview")
def get_overview():
    return overview()


@app.get("/api/products")
def get_products():
    return product_metrics()


@app.get("/api/customers/segments")
def get_segments():
    return customer_segments()


@app.get("/api/funnel")
def get_funnel():
    return funnel()


@app.get("/api/insights")
def get_insights():
    return generate_insights()


@app.get("/api/health")
def health():
    return {
        "name": "Ecomlytics",
        "status": "running",
        "version": "1.0.0",
        # If this doesn't say .../Ecomlytics_Project/app.py, you are
        # NOT running the file you think you're running — check for
        # backend/main.py or a nested project copy being launched
        # instead. See PROJECT_STATE.md.
        "entrypoint": str(Path(__file__).resolve()),
    }


# ============================================================
# DATA SOURCES / GOOGLE ANALYTICS
# ============================================================
#
# Honest connection state only. Nothing here claims to be "Live"
# unless real GOOGLE_CLIENT_ID/SECRET/REDIRECT_URI are set.
# ============================================================

@app.get("/api/data-sources")
def get_data_sources():
    return {"sources": list_data_sources()}


@app.get("/api/data-sources/google/status")
def google_analytics_status():
    """
    Standalone status for just the Google Analytics source, per the
    target route list. `/api/data-sources` (above) already includes
    this same object inside its `sources` array — this is a
    convenience alias for callers that only care about GA4, not a
    second source of truth.
    """
    return oauth_service.status()


@app.post("/api/data-sources/google/connect")
def connect_google_analytics():
    """
    JSON variant: returns the consent URL so frontend JS can redirect
    the browser itself (window.location.href = ...). This is what
    frontend/js/app.js currently calls — kept unchanged.
    """
    try:
        url = oauth_service.start_connect()
        return {"authorization_url": url}
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/api/data-sources/google/connect")
def connect_google_analytics_redirect():
    """
    Plain-link variant, for the target route list: a normal <a
    href="/api/data-sources/google/connect"> works with no JS at all,
    since a GET here redirects the browser straight to Google's
    consent screen. Same underlying oauth_service.start_connect()
    call as the POST version above — just a different response type
    for a different calling convention.
    """
    try:
        url = oauth_service.start_connect()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return RedirectResponse(url)


@app.get("/api/data-sources/google/callback")
def google_analytics_callback(code: str | None = None, state: str | None = None,
                               error: str | None = None):
    """
    Google redirects the user's browser here after consent. We can't
    show JSON to a human mid-redirect in a useful way, so we complete
    (or fail) the connection server-side and send them back to the
    Data Sources page with a short status flag it can read and show
    a toast for — the page itself always re-fetches real state from
    GET /api/data-sources rather than trusting the query string.
    """
    target = "/pages/data-sources.html"

    if error:
        return RedirectResponse(f"{target}?ga_status=denied")

    if not oauth_service.validate_state(state):
        return RedirectResponse(f"{target}?ga_status=invalid_state")

    if not code:
        return RedirectResponse(f"{target}?ga_status=missing_code")

    try:
        oauth_service.complete_connect(code)
    except GoogleAnalyticsAPIError:
        return RedirectResponse(f"{target}?ga_status=token_exchange_failed")

    return RedirectResponse(f"{target}?ga_status=connected")


@app.delete("/api/data-sources/{source_id}")
def disconnect_data_source(source_id: str):
    if source_id != "google_analytics":
        raise HTTPException(status_code=404, detail="Unknown data source.")
    oauth_service.disconnect()
    return {"success": True, "data": {"id": source_id, "state": "disconnected"}}


@app.post("/api/data-sources/google/disconnect")
def disconnect_google_analytics():
    """
    Alias for the target route list. Same effect as
    DELETE /api/data-sources/google_analytics above — kept as a
    separate thin route rather than a redirect, since browsers can't
    redirect a POST to a DELETE.
    """
    oauth_service.disconnect()
    return {"success": True, "data": {"id": "google_analytics", "state": "disconnected"}}


@app.get("/api/analytics/ga4-overview")
def ga4_overview(days: int = 30):
    """
    The first real GA4-backed metric endpoint. Returns the API design
    envelope from NEXT_INCREMENT.md section 17 — success/data/meta or
    success/error — rather than the older flat shape the demo
    endpoints still use, since this is new surface area.
    """
    try:
        data = ga4_service.fetch_overview(days=days)
        return {
            "success": True,
            "data": data["metrics"],
            "meta": {
                "source": "ga4",
                "property_id": data["property_id"],
                "date_range": data["date_range"],
            },
        }
    except RuntimeError as exc:
        return {
            "success": False,
            "error": {"code": "GA4_NOT_CONNECTED", "message": str(exc)},
        }
    except GoogleAnalyticsAPIError as exc:
        code = "GA4_UNAUTHORIZED" if exc.status_code == 401 else "GA4_REQUEST_FAILED"
        return {
            "success": False,
            "error": {"code": code, "message": str(exc)},
        }


# ============================================================
# STATIC FILES
# ============================================================
#
# Serves:
#
# /css/style.css
# /js/app.js
# /favicon.svg
# /pages/...
#
# API routes and explicit page routes above take priority.
# ============================================================

app.mount(
    "/",
    StaticFiles(
        directory=str(FRONTEND_DIR),
        html=True,
    ),
    name="frontend",
)


# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )