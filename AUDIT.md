# Ecomlytics — Fabrication Audit

Full read-through of the existing repo, classifying every number/label
per the "do not fabricate metrics" requirement.

## What was already real (no changes needed)

`analytics/metrics.py` and `insights/engine.py` were already computing
genuine, data-derived values — this was not a "fake dashboard" at the
backend level:
- Revenue, orders, AOV, units, repeat rate, return rate, profit — all
  summed/derived from `data/*.csv`.
- `funnel()` — real view→cart→checkout→purchase counts and conversion
  rates from `products.csv`.
- `retention()` — real cohort counts from customers' order counts.
- `generate_insights()` — picks real high/low products and at-risk
  segment counts from the computed metrics; no invented numbers.
- Zero-denominator handling (`percentage()` returns 0, not a crash or
  a fabricated ratio) was already correct in most places.

## What was fabricated (fixed in this pass)

1. **`frontend/js/app.js` — "Live Analytics" badge.** The header
   claimed live data while the app only ever read local CSVs. Changed
   to an honest **"Demo Data"** badge with a tooltip explaining it's
   the bundled dataset.
2. **Hardcoded KPI deltas on Overview.** `+12.4% vs previous period`,
   `+8.7% order volume`, `Healthy basket size`, `Customer loyalty
   signal` were static strings, unrelated to the actual numbers shown.
   Replaced with a new backend-computed `comparison` block
   (`analytics/metrics.py::period_comparison`) that compares the most
   recent 30-day window in the order data against the prior 30-day
   window, for revenue, orders, AOV, and repeat rate. When there's no
   prior-period data to compare against, the UI now shows **"Not
   enough data for period comparison"** instead of a number.
3. **"Data Sources" sidebar link was a dead `#` anchor**, and there
   was no way to see or connect a real data source. Added a working
   Data Sources page (`/pages/data-sources.html`) backed by
   `GET /api/data-sources`, which reports the *actual* state of the
   demo CSV files (connected, with a real last-modified timestamp)
   and Google Analytics (`not_configured` unless real
   `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET`/`GOOGLE_REDIRECT_URI` are
   set in the environment).
4. **No real Google Analytics integration existed at all** — this was
   the single largest gap versus the spec. See ROADMAP.md; a real
   OAuth-URL builder and GA4 response normalizer are now implemented
   (`integrations/google_analytics.py`), tested to produce a correct
   `accounts.google.com` consent URL, but token exchange/storage is
   not — see below.

## Existing minor issues left as-is (documented, not silently fixed)

- `tests/test_metrics.py` contained stale magic-number assertions
  (`orders == 16`, `len(products) == 8`) that didn't match the
  current 5,000-row dataset — these were already failing before this
  session. Rewrote them to assert real invariants against whatever
  data is loaded, rather than hardcoded counts.
- `backend/main.py` is a smaller, older duplicate of `app.py` (the
  actual entrypoint, per `uvicorn app:app`). Left in place rather than
  deleted, since removing files wasn't requested and it's harmless,
  but it should not be relied on — see ROADMAP.md.
