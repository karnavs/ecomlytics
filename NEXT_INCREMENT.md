# Ecomlytics — NEXT INCREMENT

## Purpose

This document is the structural roadmap for the next stages of Ecomlytics. Work incrementally, test after each major phase, and preserve working functionality before adding new features.

## Current Baseline

- Product: Ecomlytics
- Backend: Python + FastAPI
- Frontend: HTML/CSS/vanilla JavaScript
- Local development: Windows + VS Code + Python venv
- Database direction: PostgreSQL
- Demo/CSV analytics currently exist
- Real GA4 integration is being configured

### Google configuration

- Google Cloud project: `Ecomlytics`
- Project ID: `ecomlytics`
- Project number: `437244028026`
- GA4 Property ID: `555091829`
- Google Analytics Data API: enabled
- OAuth client: `Ecomlytics Local Development`
- Local callback:
  `http://localhost:8000/api/data-sources/google/callback`

### Environment variables

```env
APP_ENV=development
SECRET_KEY=

GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:8000/api/data-sources/google/callback
GA4_PROPERTY_ID=555091829

DATABASE_URL=
FRONTEND_URL=
```

Never commit `.env`. Keep `.env.example` as the safe template.

---

# 1. Immediate Audit

Before changing architecture:

- [ ] Inspect the complete repository.
- [ ] Run the existing test suite and record the baseline.
- [ ] Find hardcoded/fake analytics values.
- [ ] Find duplicate frontend/API logic.
- [ ] Find current authentication/session behavior.
- [ ] Find existing Data Sources and Google OAuth code.
- [ ] Find all database access.
- [ ] Find loading/error/empty states.
- [ ] Check all environment variables and their consumers.

Do not refactor blindly.

---

# 2. Configuration

Create one clear configuration layer.

- [ ] Centralize environment loading.
- [ ] Validate required configuration.
- [ ] Separate development/demo/production settings.
- [ ] Keep secrets server-side.
- [ ] Keep `.env.example` synchronized with real configuration.
- [ ] Document every environment variable.

---

# 3. Backend Architecture

Move toward:

```text
backend/
├── main.py
├── config.py
├── api/
│   ├── routes/
│   │   ├── analytics.py
│   │   ├── data_sources.py
│   │   ├── auth.py
│   │   └── exports.py
│   └── dependencies.py
├── services/
│   ├── analytics_service.py
│   ├── ga4_service.py
│   ├── oauth_service.py
│   ├── insight_service.py
│   └── export_service.py
├── models/
├── schemas/
└── utils/
```

Rules:
- Routes stay thin.
- Business logic goes in services.
- Validation goes in schemas.
- External APIs are isolated behind services.
- Errors are handled consistently.

---

# 4. Complete Google Analytics 4 Integration

This is the first major functional milestone.

Target flow:

```text
Ecomlytics
  ↓
Connect Google Analytics
  ↓
Google OAuth consent
  ↓
Callback
  ↓
Validate state
  ↓
Exchange code
  ↓
Store token securely
  ↓
GA4 Data API
  ↓
Property 555091829
  ↓
Real analytics data
```

Implement:

- [ ] Connect Google Analytics UI.
- [ ] OAuth authorization route.
- [ ] OAuth callback.
- [ ] State/CSRF protection.
- [ ] Token exchange.
- [ ] Secure token storage.
- [ ] Token refresh.
- [ ] Disconnect/revoke flow.
- [ ] GA4 service abstraction.
- [ ] Real `runReport` calls.
- [ ] API error/quota handling.
- [ ] No access/refresh tokens in logs.

Initial metrics:

- Users
- New users
- Sessions
- Engagement rate
- Event count
- Key events/conversions where available
- Revenue where available
- Purchase data where available

Do not show a metric when the source cannot provide enough data.

---

# 5. Data Source Abstraction

Do not couple the dashboard permanently to GA4.

Create a normalized interface:

```text
AnalyticsDataSource
├── Demo/CSV
├── Google Analytics 4
└── Future integrations
```

Conceptually:

```text
get_overview()
get_sales()
get_products()
get_customers()
get_retention()
get_funnel()
```

Every response should identify its source:

```text
source = demo
source = csv
source = ga4
```

Never silently mix fake and real data.

---

# 6. Data Sources Page

Build a proper connection UI.

Connected:

```text
Google Analytics 4
Status: Connected
Property: 555091829
Last synced: ...
[Refresh] [Disconnect]
```

Disconnected:

```text
Google Analytics 4
Status: Not connected
[Connect Google Analytics]
```

Show:
- Status
- Property
- Last sync
- Last error
- Refresh
- Disconnect/reconnect
- Available metrics/limitations

---

# 7. Database and Persistence

Move to PostgreSQL with migrations.

Initial entities:

```text
users
workspaces
workspace_members
data_sources
oauth_connections
reports
saved_reports
audit_events
```

Requirements:

- [ ] Migrations
- [ ] Foreign keys
- [ ] Timestamps
- [ ] Appropriate indexes
- [ ] Workspace isolation
- [ ] Secure token metadata
- [ ] No unnecessary stored Google data

---

# 8. Authentication and Workspace Model

Replace the demo login with real authentication.

Target:

```text
User
  ↓
Workspace
  ↓
Data Sources
  ↓
Reports / Analytics
```

Support eventually:

- User identity
- Sessions
- Logout
- Workspace ownership
- Membership
- Roles
- Protected API routes

Possible roles:

```text
Owner
Admin
Member
Viewer
```

---

# 9. Frontend Structure

Keep vanilla JS if appropriate, but modularize it:

```text
frontend/
├── pages/
├── css/
│   ├── style.css
│   ├── components.css
│   └── pages/
├── js/
│   ├── api.js
│   ├── auth.js
│   ├── state.js
│   ├── components/
│   ├── pages/
│   └── utils/
└── assets/
```

Avoid:
- Large inline scripts
- Duplicate fetch logic
- Duplicate chart formatting
- Hardcoded metrics

---

# 10. Dashboard Data Flow

Use:

```text
Frontend
  ↓
API client
  ↓
FastAPI route
  ↓
Analytics service
  ↓
Selected data source
  ↓
Normalized response
  ↓
Visualization
```

The frontend must never call Google APIs directly.

---

# 11. Analytics Pages

## Overview

- Revenue
- Orders/purchases
- Users
- Sessions
- Conversion rate where supported
- AOV where supported
- Trends
- Period comparison
- Date selector
- Data-source indicator

## Sales

- Revenue over time
- Orders over time
- Channel/source performance
- Conversion trends
- Period comparison

## Products

- Top products
- Revenue contribution
- Purchase count
- Product trends

If GA4 cannot provide a required dimension, show the limitation instead of inventing data.

## Customers

- New vs returning users
- Engagement
- Segmentation where supported
- Repeat behavior only when backed by actual data

## Retention/Funnel

Only show calculations supported by available source events.

---

# 12. Evidence-Based Insight Engine

Use:

```text
Raw analytics
  ↓
Validated metrics
  ↓
Trend detection
  ↓
Anomaly detection
  ↓
Business rules
  ↓
Insight
  ↓
Optional AI explanation
```

Every insight should contain:

- Title
- Observation
- Evidence
- Time period
- Metric
- Change
- Possible interpretation
- Suggested investigation/action
- Confidence

AI must never invent metrics or trends.

---

# 13. Reporting and Export

Add:

- [ ] CSV export
- [ ] PDF/report export
- [ ] Date ranges
- [ ] Saved reports
- [ ] Shareable reports later
- [ ] Scheduled reports later

Reports should contain:
- Source
- Date range
- Generated time
- Metrics
- Charts
- Insights
- Limitations

---

# 14. UX States

Every page should support:

```text
Loading
Success
Empty
Error
Not configured
```

Examples:

```text
Loading analytics...

No purchase data is available for this period.

Google Analytics could not be reached.
[Try again]

Google Analytics is not connected.
[Connect Google Analytics]
```

Never leave blank or broken cards.

---

# 15. UI/UX Quality

Keep the Ecomlytics visual identity.

Improve:

- Consistent spacing
- Typography
- Visual hierarchy
- Reusable cards/buttons/badges
- Responsive sidebar/navigation
- Mobile layout
- Accessibility
- Keyboard focus
- Tooltips
- Date controls
- Data-source badges

Avoid turning the product into generic AI-dashboard boilerplate.

---

# 16. Security

Before production:

- [ ] `.env` ignored
- [ ] No secrets in Git
- [ ] OAuth state validation
- [ ] Secure sessions
- [ ] HTTPS
- [ ] Restricted CORS
- [ ] Input validation
- [ ] Rate limiting where appropriate
- [ ] No token/password logging
- [ ] Safe error messages
- [ ] Security headers
- [ ] Dependency audit
- [ ] Token encryption at rest if persisted

---

# 17. API Quality

Use predictable responses.

Success:

```json
{
  "success": true,
  "data": {},
  "meta": {
    "source": "ga4",
    "property_id": "555091829",
    "date_range": {}
  }
}
```

Error:

```json
{
  "success": false,
  "error": {
    "code": "GA4_NOT_CONNECTED",
    "message": "Google Analytics is not connected."
  }
}
```

Never expose stack traces to users.

---

# 18. Testing

## Unit
- [ ] Analytics calculations
- [ ] Date ranges
- [ ] Data normalization
- [ ] Insight rules
- [ ] Configuration validation

## Integration
- [ ] OAuth callback
- [ ] Token handling
- [ ] GA4 service
- [ ] API routes
- [ ] Database

## Critical user flow

```text
Login
→ Dashboard
→ Data Sources
→ Connect GA4
→ Analytics
→ Disconnect
```

Run tests after every major structural change.

---

# 19. Observability

Add structured events such as:

```text
application_started
oauth_started
oauth_success
oauth_failed
ga4_request
ga4_request_failed
analytics_loaded
data_source_disconnected
report_generated
```

Never log secrets, access tokens, refresh tokens, passwords, or session secrets.

---

# 20. Performance

After correctness:

- [ ] Cache expensive analytics queries
- [ ] Avoid duplicate API calls
- [ ] Batch GA4 requests where appropriate
- [ ] Lazy-load noncritical dashboard sections
- [ ] Optimize DB queries
- [ ] Add indexes based on real query patterns

Do not optimize prematurely.

---

# 21. Deployment

Use:

```text
Local
  ↓
Test
  ↓
Staging
  ↓
Production
```

Production checklist:

- [ ] Production domain
- [ ] HTTPS
- [ ] Production environment variables
- [ ] Production database
- [ ] Production OAuth redirect URI
- [ ] Authorized domain in Google OAuth
- [ ] CORS configuration
- [ ] Secure cookies/session settings
- [ ] Database migrations
- [ ] Health endpoint
- [ ] Logging/monitoring

Keep the localhost OAuth URI for development and add the production URI separately.

---

# 22. Documentation

Maintain:

```text
README.md
.env.example
NEXT_INCREMENT.md
SESSION_HANDOFF.md
CONTINUE_PROMPT.md
```

README should cover:
- Architecture
- Setup
- Environment variables
- Database
- Google Cloud/GA4
- OAuth
- Running locally
- Testing
- Deployment
- Troubleshooting

---

# 23. Implementation Order

## Phase 1 — Stabilize
- [ ] Repository audit
- [ ] Baseline tests
- [ ] Configuration validation
- [ ] Remove fake/hardcoded analytics where appropriate
- [ ] Confirm `.env` security
- [ ] Confirm backend health

## Phase 2 — Complete GA4
- [ ] OAuth route
- [ ] Callback
- [ ] Token handling
- [ ] GA4 service
- [ ] Real `runReport`
- [ ] Data-source status
- [ ] First real metric in dashboard

## Phase 3 — Normalize
- [ ] Data-source abstraction
- [ ] Shared response schema
- [ ] Demo/GA4 separation
- [ ] Shared date-range handling

## Phase 4 — Backend
- [ ] Routes
- [ ] Services
- [ ] Schemas
- [ ] Models
- [ ] Error handling
- [ ] Logging

## Phase 5 — Persistence
- [ ] PostgreSQL
- [ ] Migrations
- [ ] Users
- [ ] Workspaces
- [ ] Data sources
- [ ] OAuth connections

## Phase 6 — Dashboard
- [ ] Overview
- [ ] Sales
- [ ] Products
- [ ] Customers
- [ ] Retention/funnel
- [ ] Loading/error/empty states

## Phase 7 — Insights
- [ ] Rule-based insights
- [ ] Evidence model
- [ ] Trends
- [ ] Anomalies
- [ ] Optional LLM explanation

## Phase 8 — Reporting
- [ ] CSV
- [ ] PDF
- [ ] Saved reports

## Phase 9 — Security
- [ ] Authentication
- [ ] Authorization
- [ ] Token protection
- [ ] CORS
- [ ] Rate limiting
- [ ] Security audit

## Phase 10 — Deployment
- [ ] Staging
- [ ] Production
- [ ] Production OAuth
- [ ] Production database
- [ ] Monitoring
- [ ] Final documentation

---

# 24. Definition of Done

Ecomlytics is not production-ready until:

- [ ] Real GA4 data can be connected.
- [ ] OAuth works reliably.
- [ ] Tokens are handled securely.
- [ ] Dashboard values are real or explicitly labeled demo data.
- [ ] No fake metrics are presented as real.
- [ ] Backend is modular.
- [ ] Database persistence works.
- [ ] Authentication works.
- [ ] Workspace isolation works.
- [ ] Errors/loading/empty states work.
- [ ] Tests pass.
- [ ] Secrets are protected.
- [ ] Production deployment works.
- [ ] Production OAuth redirect works.
- [ ] README works from a clean setup.

---

# 25. AI/Coding-Agent Rules

When continuing Ecomlytics:

1. Inspect before editing.
2. Preserve working functionality.
3. Do not rewrite the entire project unnecessarily.
4. Make one logical change at a time.
5. Run tests after structural changes.
6. Never invent analytics data.
7. Keep demo data separate from real data.
8. Never expose secrets.
9. Never hardcode OAuth credentials.
10. Check existing environment-variable values before changing them.
11. Do not remove features without documenting the replacement.
12. Create a checkpoint before major changes.
13. Keep this roadmap updated.
14. Near context/session limits, **PROJECT PRESERVATION > NEW FEATURES**.
15. Before ending a session, create/update `SESSION_HANDOFF.md` and `CONTINUE_PROMPT.md` when needed.

---

# 26. Immediate Next Action

The next task is **not** another UI feature.

First audit the existing Ecomlytics implementation and determine exactly what already exists for:

- Google OAuth authorization route
- Google OAuth callback
- Token storage/refresh
- GA4 service
- Data Sources UI
- Analytics API routes
- Existing demo/CSV data flow

Then implement only the missing pieces.

## First end-to-end milestone

```text
Ecomlytics
  ↓
Connect Google Analytics
  ↓
Google OAuth
  ↓
Callback
  ↓
Authenticated GA4 request
  ↓
Property 555091829
  ↓
Real GA4 metric
  ↓
Dashboard
```

Complete this path and test it before moving to the larger architecture changes.
