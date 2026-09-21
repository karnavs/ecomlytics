# Ecomlytics — PROJECT_STATE

## Current Increment

**Increment:** NEXT_INCREMENT.md Phase 1 (stabilize) + the first
slice of Phase 2 (Complete GA4 integration) — specifically the "First
end-to-end milestone" in NEXT_INCREMENT.md §26:
Connect → Google OAuth → Callback → Authenticated GA4 request →
Property 555091829 → Real GA4 metric → Dashboard.

**Completed this increment:**
- Fixed a real bug found during the audit: `config.py` read
  `os.environ.get("555091829", "")` instead of
  `os.environ.get("GA4_PROPERTY_ID", "")` — the GA4 property ID was
  never actually being read from the environment. There's now a
  regression test for this (`test_config_ga4_property_id_reads_correct_env`).
- OAuth CSRF state: generated per connect attempt, single-use,
  10-minute TTL, validated on callback (`services/oauth_service.py`).
- Real authorization-code → token exchange
  (`integrations/google_analytics.exchange_code_for_tokens`), real
  refresh-token exchange, real token revocation call — all via `httpx`
  against Google's actual endpoints.
- Token storage: SQLite (`db/token_store.py`), Fernet-encrypted at
  rest (key derived from `SECRET_KEY`, or a generated
  `data/.token_key` file if `SECRET_KEY` isn't set), against a fixed
  `workspace_id="demo"` — explicitly a placeholder ahead of real
  multi-tenancy, not a real isolation boundary.
- Real GA4 Data API `runReport` call
  (`integrations/google_analytics.run_report`) with proper 401/429/
  other-error handling that never leaks Google's raw response to the
  frontend.
- `services/ga4_service.py`: fetches a live GA4 overview
  (`activeUsers`, `newUsers`, `sessions`, `engagedSessions`,
  `engagementRate`, `eventCount`) for the connected property, tagged
  `source: "ga4"`.
- New/changed API routes: `POST /api/data-sources/google/connect`,
  `GET /api/data-sources/google/callback` (now does real work instead
  of a 501 stub), `DELETE /api/data-sources/{id}`,
  `GET /api/analytics/ga4-overview` (uses the `{success, data, meta}`
  / `{success: false, error}` envelope from NEXT_INCREMENT.md §17 —
  the older demo endpoints still use their original flat shape; that
  broader migration wasn't part of this increment).
- Frontend: Data Sources page now shows a connect/disconnect button
  based on real state, a toast for the OAuth redirect result
  (`?ga_status=...`), and a live metrics preview once connected.

**Not completed / explicitly out of scope for this increment:**
- Everything in NEXT_INCREMENT.md Phases 3–10 (data-source
  abstraction beyond GA4/CSV, full backend module split, Postgres,
  real user auth/workspaces, remaining dashboard pages wired to GA4,
  reporting/export, broader security hardening, deployment).
- `backend/main.py` is still an older, smaller duplicate of `app.py`
  (the real entrypoint) — not removed.

## Current Project State

- **Backend:** FastAPI, single `app.py` entrypoint (not yet split
  into `api/`/`services/`/`models/` per the target structure — only
  `services/` and `db/` exist so far, added this increment).
- **Frontend:** Vanilla JS/HTML/CSS, unchanged structure (not yet
  modularized per NEXT_INCREMENT.md §9).
- **Database:** SQLite only, and only for OAuth tokens
  (`data/app.db`, gitignored). No Postgres, no migrations, no
  users/workspaces/customers/orders tables. All business analytics
  still reads `data/*.csv` directly.
- **Analytics:** Demo/CSV metrics unchanged from the previous
  session. GA4 metrics are real once connected, but not yet merged
  into the Overview/Sales/Products/Customers/Retention pages — only
  the Data Sources page shows a live GA4 preview right now.
- **Authentication:** Still the original `localStorage` demo login —
  untouched. The new OAuth token store has no concept of "which user"
  beyond the fixed `demo` workspace.

## Files Changed / Added This Increment

- Fixed: `config.py` (GA4_PROPERTY_ID bug)
- Added: `db/__init__.py`, `db/token_store.py`
- Added: `services/__init__.py`, `services/oauth_service.py`,
  `services/ga4_service.py`
- Changed: `integrations/google_analytics.py` (added real token
  exchange/refresh/revoke/runReport calls; kept the existing
  `build_authorization_url`/`normalize_report`)
- Changed: `integrations/data_sources.py` (now sources GA status from
  `services.oauth_service.status()` instead of the old stateless
  `google_analytics.status()`)
- Changed: `app.py` (real connect/callback/disconnect/ga4-overview
  routes)
- Changed: `frontend/js/app.js`, `frontend/css/style.css` (Data
  Sources page: disconnect button, OAuth-result toast, live preview)
- Added: `tests/test_oauth_ga4.py` (15 tests, all passing, no real
  network calls — Google's HTTP calls are monkeypatched)
- Changed: `requirements.txt` (+`httpx`, +`cryptography`),
  `.env.example` (+`TOKEN_STORE_PATH` note), `.gitignore`
  (+`data/app.db`, +`data/.token_key`)

## Testing

- `pytest tests/` — **15/15 passed** (5 from the previous session's
  `test_metrics.py`, 10 new in `test_oauth_ga4.py`).
- Manually ran the app locally (`uvicorn app:app`) and verified with
  `curl`:
  - `/api/data-sources` correctly reports `not_configured` with no
    `.env`, and `disconnected`/`connected`/property ID once
    credentials are set.
  - `POST /api/data-sources/google/connect` returns a real, correctly
    formed `accounts.google.com` consent URL.
  - `GET /api/data-sources/google/callback` with a wrong `state`
    correctly redirects with `ga_status=invalid_state` **without**
    attempting a network call (CSRF check happens first).
  - The same callback with a *valid* state and a fake `code` attempts
    the real token exchange, which — in this sandboxed environment
    with no access to `googleapis.com` — times out and redirects with
    `ga_status=token_exchange_failed`, and leaves no partial/corrupt
    connection behind. **This is the one thing that could not be
    tested against the real Google API**, since this environment has
    no network access to Google's endpoints; it was verified instead
    with monkeypatched HTTP calls in `tests/test_oauth_ga4.py` and a
    manual Python script exercising the full
    connect → store → fetch_overview → normalize path with a faked
    successful token/response (see session transcript). **Karna should
    do one real end-to-end test locally** with the actual
    `GOOGLE_CLIENT_ID`/`SECRET` before considering this done.
  - `DELETE /api/data-sources/google_analytics` correctly clears the
    stored connection; `DELETE /api/data-sources/nonsense` returns
    404.
  - `/api/overview`, `/api/products`, etc. (previous session's work)
    still respond 200 — nothing broken.

## Known Issues / Limitations

- **CSRF state store is in-memory** (`services/oauth_service._pending_states`).
  Fine for one local dev process; will silently break (all callbacks
  rejected as invalid) across a server restart or multiple workers.
  Needs to move to the DB/Redis once real deployment is in scope.
- Token store's "workspace" is a hardcoded constant (`demo`) — not
  real multi-tenancy.
- GA4 metrics aren't merged into the main Overview dashboard yet,
  only previewed on the Data Sources page.
- **Security note (not a code issue, but important):** the ZIP you
  uploaded this turn (`Ecomlytics_Project_updated__2_.zip`) contained
  a real `.env` file with what appear to be actual
  `GOOGLE_CLIENT_SECRET`/`SECRET_KEY` values, plus an unrelated
  `data/pythagora.log` file from your editor tooling. Neither is
  included in this delivered ZIP. If that client secret has been
  shared anywhere else (git history, another chat, etc.), consider
  rotating it in Google Cloud Console — OAuth client secrets are not
  meant to leave your machine.

## Next Work

1. Do one real local test of the connect → callback → GA4 metric flow
   with actual Google credentials (this environment can't reach
   `googleapis.com`, so it's untested against the real API).
2. Wire `services/ga4_service.fetch_overview()` into the actual
   Overview page (behind the existing `source` labeling pattern) so
   GA4-connected workspaces see it in the main dashboard, not just the
   Data Sources preview.
3. Move the CSRF state store out of an in-memory dict before this
   goes anywhere beyond one local dev process.
4. Continue down NEXT_INCREMENT.md in order — Phase 3 (data-source
   abstraction) is the natural next step, then Phase 5
   (Postgres/persistence), since auth/workspaces block most of what's
   left.
