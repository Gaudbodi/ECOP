# Context (DOC Intel)

> Running notes extracted from descriptive documentation. These describe the *current* state of the codebase / project, not target requirements. Verbatim with attribution.

---

## Current Project Identity

source: CLAUDE.md §"Project Overview"

Ghana National CAP (Common Alerting Protocol) Platform — a Flask + Socket.IO backend that ingests weather/emergency alerts (from GMeT webhook or manual entry), enriches them (geo-resolution, translation, TTS), routes them through a generator → validator → dispatch workflow, and dispatches via MNO webhook + Twilio SMS.

---

## Active Entry Point

source: CLAUDE.md §"Project Overview"

- Active entry point: **`ghana_cap_app.py`** (NOT `app.py`)
- `app.py` has been deleted in the working tree
- `app[DEPRECATED].py` is the legacy single-file version, kept only for reference
- `Procfile` and `Dockerfile` still reference `app:app` — STALE, must be updated when deploying (do not revert the rename)

---

## Running the App

source: CLAUDE.md §"Running the App"

- Dev: `python ghana_cap_app.py` — Socket.IO via eventlet, port 5000
- Prod: `gunicorn --worker-class eventlet -w 1 ghana_cap_app:app` (override Procfile)
- Login URL: http://localhost:5000/login
- Auth scheme: email + 6-digit code
- If `SMTP_USERNAME` is unset, code is logged to stdout instead of emailed (see `services/email_service.py`)
- No test suite exists. Do not add a test framework unless explicitly asked.

---

## Seed Users (created/synced on every startup by `seed_users()` in `db.py`)

source: CLAUDE.md §"Running the App"

| Email | Role | Agency |
| --- | --- | --- |
| francis@example.com | Admin | NCA |
| generator@example.com | cap generator | GMeT |
| validator@example.com | cap validator | GMeT |
| nadmo_gen@example.com | cap generator | NADMO |

---

## Request → Alert Pipeline

source: CLAUDE.md §"Request → Alert pipeline"

`ghana_cap_app.process_alert_logic` is the **single funnel** for all alert ingress (GMeT webhook + manual form). Steps:

1. Generates an `identifier` if missing.
2. Calls `geo_service.resolve_location(lat, lon)` to map coordinates to Ghana regions via the GeoJSON in `static/ghana_regions.json` (Shapely point-in-polygon).
3. Calls `enrichment_service.translate_text(...)` (OpenAI `gpt-4o-mini`) for English → Twi/Hausa, then `text_to_speech(...)` (OpenAI `tts-1`) writing MP3s to `static/audio/`.
4. Persists via `db.save_alert` (Mongo `alerts` collection, upsert by `identifier`).
5. **Conditionally** dispatches: only when `workflow_stage == 3` does it call `dispatch_service.dispatch_to_mno(...)` and `dispatch_service.send_sms(...)` (Twilio, mocked when creds absent).
6. Emits `new_alert` over Socket.IO and calls `external_analytics_service.sync_alert(...)`.

---

## Workflow Stages (Critical State Machine)

source: CLAUDE.md §"Workflow stages (critical)"

The `workflow_stage` integer drives gating across the whole system. Treat it as a state machine, not a label:

- **0** — Rejected / Draft (set by `validate_alert` on rejection)
- **1** — Pending Validation (default for `cap generator` submissions)
- **3** — Dispatched (set by Admin direct submission, or by validator approval in `/api/v1/alerts/validate/<identifier>`)

`process_alert_logic` only dispatches when `workflow_stage == 3`. The validator approval endpoint re-runs dispatch and updates the alert.

If you add a new role or stage, update **all** of:
- The role check in `manual_alert` (line 135)
- The validator allowlist (line 143)
- The stage guard in `validate_alert` (line 157)
- The dispatch gate in `process_alert_logic` (line 241)

---

## Services Layer (`services/`) — Singletons + Graceful Degradation

source: CLAUDE.md §"Services layer"

Each service is a singleton instantiated at import time and imported by name from `ghana_cap_app.py`. They degrade gracefully — every external integration (OpenAI, Twilio, SMTP, MNO webhook) checks for credentials on init and falls back to mock/log behavior when absent. **App boots and the workflow runs end-to-end with zero external creds. Preserve this property when editing.**

- `geo_service.py` — Shapely + `static/ghana_regions.json`. Returns `["Ghana (General)"]` if no polygon matches.
- `enrichment_service.py` — OpenAI translate + TTS. Without `OPENAI_API_KEY`, returns `[Lang Translation Mock]: ...` strings and `/static/audio/mock_<lang>.mp3` paths.
- `dispatch_service.py` — POSTs to `MNO_WEBHOOK_URL` (default `http://localhost:5001/...`), and uses Twilio for SMS. Without `TWILIO_AUTH_TOKEN`, SMS is logged only.
- `email_service.py` — SMTP for verification codes; logs the code when SMTP creds are missing.
- `external_analytics_service.py` — Maps internal CAP fields to the PostgreSQL `analytics_alert` schema in `earlywarningdb.sql`. Currently logs only; the actual psycopg2 insert is a TODO at line 43.

---

## Persistence

source: CLAUDE.md §"Persistence"

- **MongoDB Atlas** (`fsrp_aggregator` DB) is the operational store. `db.get_db()` is a lazy singleton; collections used: `users`, `verification_codes`, `alerts`. Connection details default to a hard-coded URI in `db.py` and `.env` — overridable via `MONGO_URI` / `DB_NAME` env vars.
- **PostgreSQL** (schema in `earlywarningdb.sql`) is an **external** analytics DB owned by another team. The platform is meant to push alerts into it; mapping lives in `external_analytics_service._map_agency_id` and the `sync_alert` method. Do not run that .sql against the project's own DB — it's documentation of the target schema.

---

## Frontend

source: CLAUDE.md §"Frontend"

- Server-rendered Jinja templates with vanilla JS + Leaflet (admin map) and Socket.IO client.
- Active templates: `ghana_cap_dashboard.html`, `login.html`.
- Everything else in `templates/` (dated filenames like `1_oct_25.html`, `tv_display.html`, `3d map.html`) is historical/experimental and not wired into routes.
- Design language: glassmorphism (per the PRD).
- Real-time updates: dashboard listens for `new_alert` and `alert_updated` events on the default Socket.IO namespace.
- A `/live_feed` namespace is consumed by `data_receiver.py` (a standalone external client script — IT's downstream consumer, not part of the web app), but the **server side of `/live_feed` is not currently emitted to from `ghana_cap_app.py`**.

---

## Configuration / `.env` Keys

source: CLAUDE.md §"Configuration"

All optional — app boots without them in mocked mode:

```
MONGO_URI=...
DB_NAME=fsrp_aggregator
OPENAI_API_KEY=...
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_FROM_NUMBER=+...
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=...
SMTP_PASSWORD=...
MNO_WEBHOOK_URL=http://localhost:5001/api/v1/mno/receive
```

### Hard-Coded Values (Tech Debt)

- GMeT webhook API key check in `ghana_cap_app.py:114` is the literal string `"gh_cap_poc_key_2026"`.
- `app.config['SECRET_KEY']` is also hard-coded.
- Both should be moved to env vars before any non-PoC deployment, but **don't change them silently** — they will break the existing webhook contract with GMeT and invalidate active sessions.

---

## Project Conventions (inherited from GEMINI.md)

source: CLAUDE.md §"Conventions inherited from GEMINI.md"

- Iterate on existing code/patterns before introducing new ones; if you must replace, remove the old implementation in the same change.
- Keep files under ~300–400 lines; refactor at that point.
- No mock data in dev/prod paths — mocks are acceptable only as graceful fallbacks when an external credential is missing (the existing pattern across `services/`).
- Never overwrite `.env` without explicit confirmation.
