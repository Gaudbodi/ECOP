# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Ghana National CAP (Common Alerting Protocol) Platform — a Flask + Socket.IO backend that ingests weather/emergency alerts (from GMeT webhook or manual entry), enriches them (geo-resolution, translation, TTS), routes them through a generator → validator → dispatch workflow, and dispatches via MNO webhook + Twilio SMS. See `PRD.txt` for the full product spec.

The active entry point is **`ghana_cap_app.py`**, not `app.py`. The original `app.py` has been deleted in the working tree, and `app[DEPRECATED].py` is the legacy single-file version kept only for reference. The `Procfile` and `Dockerfile` still reference `app:app` and are stale relative to the current entry point — update them when deploying rather than reverting the rename.

## Running the App

```bash
pip install -r requirements.txt
python ghana_cap_app.py            # dev — Socket.IO via eventlet, port 5000
# or
gunicorn --worker-class eventlet -w 1 ghana_cap_app:app  # prod (override Procfile)
```

Open http://localhost:5000/login. Seed users (created/synced on every startup by `seed_users()` in `db.py`):

| Email | Role | Agency |
| --- | --- | --- |
| francis@example.com | Admin | NCA |
| generator@example.com | cap generator | GMeT |
| validator@example.com | cap validator | GMeT |
| nadmo_gen@example.com | cap generator | NADMO |

Login is **email + 6-digit code**. If `RESEND_API_KEY` is unset, the code is logged to stdout instead of emailed (see `services/email_service.py`) — read it from the server log during dev.

Tests live in `tests/` (pytest + pytest-flask, added in Phase 9). Run with `python -m pytest tests/ -q`.

## Architecture

### Request → Alert pipeline

`ghana_cap_app.process_alert_logic` is the single funnel for all alert ingress (GMeT webhook + manual form). It:

1. Generates an `identifier` if missing.
2. Calls `geo_service.resolve_location(lat, lon)` to map coordinates to Ghana regions via the GeoJSON in `static/ghana_regions.json` (Shapely point-in-polygon).
3. Calls `enrichment_service.translate_text(...)` (OpenAI `gpt-4o-mini`) for English → Twi/Hausa, then `text_to_speech(...)` (OpenAI `tts-1`) writing MP3s to `static/audio/`.
4. Persists via `db.save_alert` (Mongo `alerts` collection, upsert by `identifier`).
5. **Conditionally** dispatches: only when `workflow_stage == 3` does it call `dispatch_service.dispatch_to_mno(...)` and `dispatch_service.send_sms(...)` (Twilio, mocked when creds absent).
6. Emits `new_alert` over Socket.IO and calls `external_analytics_service.sync_alert(...)`.

### Workflow stages (critical)

The `workflow_stage` integer drives gating across the whole system. Treat it as a state machine, not a label:

- **0** — Rejected / Draft (set by `validate_alert` on rejection)
- **1** — Pending Validation (default for `cap generator` submissions)
- **3** — Dispatched (set by Admin direct submission, or by validator approval in `/api/v1/alerts/validate/<identifier>`)

`process_alert_logic` only dispatches when `workflow_stage == 3`. The validator approval endpoint re-runs dispatch and updates the alert. If you add a new role or stage, update **all** of: the role check in `manual_alert` (line 135), the validator allowlist (line 143), the stage guard in `validate_alert` (line 157), and the dispatch gate in `process_alert_logic` (line 241).

### Services layer (`services/`)

Each service is a singleton instantiated at import time and imported by name from `ghana_cap_app.py`. They degrade gracefully — every external integration (OpenAI, Twilio, SMTP, MNO webhook) checks for credentials on init and falls back to mock/log behavior when absent, so the app boots and the workflow runs end-to-end with zero external creds. Preserve this property when editing.

- `geo_service.py` — Shapely + `static/ghana_regions.json`. Returns `["Ghana (General)"]` if no polygon matches.
- `enrichment_service.py` — OpenAI translate (gpt-4o-mini) + TTS (tts-1) for every language. Without `OPENAI_API_KEY`, returns `[Lang Translation Mock]: ...` strings and `/static/audio/mock_<lang>.mp3` paths. (Khaya / Ghana NLP TTS was removed in May 2026 when ghananlp.org's public API was withdrawn.)
- `dispatch_service.py` — POSTs to `MNO_WEBHOOK_URL` (default `http://localhost:5001/...`), and uses Twilio for SMS. Without `TWILIO_AUTH_TOKEN`, SMS is logged only.
- `email_service.py` — Resend transactional email for OTP delivery. Without `RESEND_API_KEY`, the code is logged to stdout. (SMTP was replaced in May 2026.)
- `advisory_agent_service.py` — Google Gemma 4 (via Gemini API, `google-genai` SDK) with native function calling. Five tools: geocode, population density, historical alerts, severity assessment, advisory drafting. Without `GEMINI_API_KEY`, returns a clearly-marked mock CAP draft via the static geocoder. Replaces the prior Anthropic Claude integration as of May 2026.
- `sms_2fa_service.py` — Africa's Talking primary, Twilio fallback, log-only when neither is configured.
- `external_analytics_service.py` — Maps internal CAP fields to the PostgreSQL `analytics_alert` schema in `earlywarningdb.sql`. Currently logs only; the actual psycopg2 insert is a TODO at line 43.

### Persistence

- **MongoDB Atlas** (`fsrp_aggregator` DB) is the operational store. `db.get_db()` is a lazy singleton; collections used: `users`, `verification_codes`, `alerts`. Connection comes from the `MONGO_URI` / `DB_NAME` env vars (set in `.env` locally, Render dashboard in prod); the code fallback is plain `mongodb://localhost:27017` — no credentials are committed.
- **PostgreSQL** (schema in `earlywarningdb.sql`) is an **external** analytics DB owned by another team. The platform is meant to push alerts into it; mapping lives in `external_analytics_service._map_agency_id` and the `sync_alert` method. Do not run that .sql against the project's own DB — it's documentation of the target schema.

### Frontend

Server-rendered Jinja templates with vanilla JS + Leaflet (admin map) and Socket.IO client. The active templates are `ghana_cap_dashboard.html` and `login.html`; everything else in `templates/` (dated filenames like `1_oct_25.html`, `tv_display.html`, `3d map.html`) is historical/experimental and not wired into routes. The design language is glassmorphism per the PRD.

Real-time updates: the dashboard listens for `new_alert` and `alert_updated` events on the default Socket.IO namespace. There is also a `/live_feed` namespace consumed by `data_receiver.py` (a standalone external client script — IT's downstream consumer, not part of the web app), but the server side of `/live_feed` is not currently emitted to from `ghana_cap_app.py`.

## Configuration

`.env` keys (all optional — app boots without them in mocked mode). See `.env.example` for the canonical, fully-commented template:

```
FLASK_SECRET_KEY=...
GMET_WEBHOOK_API_KEY=...
MONGO_URI=...
DB_NAME=fsrp_aggregator
OPENAI_API_KEY=...
GEMINI_API_KEY=...                    # Google AI Studio key for Gemma 4 advisory agent
GEMINI_MODEL=gemma-4-26b-a4b-it       # default; alternate: gemma-4-31b-it
RESEND_API_KEY=...                    # Resend transactional email (OTP delivery)
RESEND_FROM=Ghana CAP Platform <onboarding@resend.dev>
AFRICASTALKING_USERNAME=sandbox
AFRICASTALKING_API_KEY=...
AFRICASTALKING_FROM=...
TWILIO_ACCOUNT_SID=...                # fallback SMS only
TWILIO_AUTH_TOKEN=...
TWILIO_FROM_NUMBER=+...
MNO_WEBHOOK_URL=http://localhost:5000/public/feed/receive
ALLOWED_ORIGINS=http://localhost:5000,http://localhost:5173
```

Hard-coded values to be aware of: the GMeT webhook API key check in `ghana_cap_app.py:114` is the literal string `"gh_cap_poc_key_2026"`, and `app.config['SECRET_KEY']` is also hard-coded. Both should be moved to env vars before any non-PoC deployment, but don't change them silently — they will break the existing webhook contract with GMeT and invalidate active sessions.

## Conventions inherited from GEMINI.md

- Iterate on existing code/patterns before introducing new ones; if you must replace, remove the old implementation in the same change.
- Keep files under ~300–400 lines; refactor at that point.
- No mock data in dev/prod paths — mocks are acceptable only as graceful fallbacks when an external credential is missing (the existing pattern across `services/`).
- Never overwrite `.env` without explicit confirmation.
