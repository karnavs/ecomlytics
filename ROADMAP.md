# Ecomlytics — Roadmap / Next Steps

This session made the backend numbers honest and started the real
Google Analytics integration. It did **not** attempt the full
production rebuild the original brief describes — that's a multi-week
effort. Below is what's done, what's stubbed, and what's left, in
priority order.

## Done this session (see AUDIT.md for details)
- Real 30-day period-over-period comparison (`period_comparison()`),
  wired into `/api/overview` and the Overview KPI cards.
- "Live Analytics" → "Demo Data" label fix.
- `GET /api/data-sources` + working Data Sources page, showing real
  connection state for the CSV dataset and Google Analytics.
- Real Google OAuth consent-URL builder and GA4 response normalizer
  (`integrations/google_analytics.py`) — tested, produces a correct
  `accounts.google.com/o/oauth2/v2/auth` URL once credentials are set.
- Fixed two stale/broken tests; all tests pass (`pytest tests/`).

## Not done — recommended priority order

1. **Auth + workspace model.** Nothing here is multi-tenant yet, and
   there's no real login (still `localStorage`-based demo auth). This
   blocks everything else that's "per customer" (data source
   ownership, saved GA tokens). Suggested: FastAPI + `passlib`
   (bcrypt) for password hashing, JWT access tokens, a `users` +
   `workspaces` table.
2. **A real database.** `database/schema.sql` only has 3 bare tables
   and nothing writes to it — the app is 100% CSV-read-only today.
   Needs the fuller schema from the brief (users, workspaces,
   data_sources, google_analytics_connections, sync_jobs,
   analytics_snapshots, insights) plus a migration tool (Alembic).
   SQLite is a reasonable local-dev stand-in before Postgres.
3. **OAuth token exchange + storage.** `build_authorization_url()`
   exists; the token exchange call to
   `integrations/google_analytics.py::TOKEN_URL` and persisting
   tokens against a workspace still need the DB from #2. The
   `/api/data-sources/google/callback` route currently returns a
   correct `501` explaining this rather than pretending to succeed —
   that's the honest state to build on.
4. **GA4 Data API querying + normalization into daily_metrics**, once
   #3 exists — `normalize_report()` is already written and unit-
   testable against a sample GA4 API response shape.
5. **Backend module split** (`api/`, `services/`, `models/`,
   `schemas/`) — current `app.py` is manageable in size but will need
   this once auth/DB land.
6. **Frontend**: Sales/Products/Customers/Retention pages still use
   the original simpler UI; date-range picker, filters, RFM
   segmentation, CSV/PDF export, and the broader visual-polish pass
   from the brief haven't been touched.
7. Cleanup: `backend/main.py` is a smaller duplicate of `app.py` (the
   real entrypoint per `uvicorn app:app`) — worth deleting once
   confirmed unused. There's also a nested, seemingly-unused
   `Ecomlytics_Complete_Project/` copy of the whole project inside
   this folder from the original upload — worth confirming with
   Karna whether it can be deleted.

## Running it locally
```
python -m venv venv
venv\Scripts\Activate.ps1        # Windows PowerShell
pip install -r requirements.txt
uvicorn app:app --reload
```
Open http://127.0.0.1:8000 — runs in demo mode with no `.env` needed.
Copy `.env.example` to `.env` and fill in `GOOGLE_CLIENT_ID` /
`GOOGLE_CLIENT_SECRET` / `GOOGLE_REDIRECT_URI` to unlock the Google
Analytics "Connect" flow's authorization step (token exchange still
needs #3 above).
