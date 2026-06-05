# Ghana National CAP Platform

## What This Is

A Flask + Socket.IO backend (Python) plus a React + Vite + TypeScript frontend (Phase 4+) that ingests weather/emergency alerts (from the Ghana Meteorological Agency webhook or manual operator entry assisted by an AI advisory agent), enriches them with geo-resolution against Ghanaian administrative boundaries, English to Twi/Hausa translation with native-quality voices, and TTS audio, and dispatches them as CAP v1.2 payloads to Mobile Network Operator (MNO) webhooks, SMS to pre-registered test numbers, and a public TV-display feed. The platform is the **National Emergency Nexus** — operated by NCA, with GMeT as the primary alert source, selected MNOs as the dispatch target, and FM broadcasters / public displays as downstream consumers.

The original GMeT End-to-End PoC scope (PRD.txt) remains the foundation; the broader overhaul scope (real 2FA via Africa's Talking, AI advisory agent, frontend migration to React, Mapbox map UX with natural-language geocoding, react-globe.gl background, public display, automated tests) was absorbed locally on 2026-05-09 after the cloud `/ultraplan` session failed.

## Core Value

A national emergency nexus that auto-dispatches GMeT alerts within 5 seconds, lets operators draft alerts in natural language with AI assistance ("heavy rain expected at Osu in Accra" → pre-filled CAP JSON + map zoom + rain overlay), broadcasts to telecom operators + a public TV-display URL, and is hardened for production with real 2FA + automated tests.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

(None yet — PoC milestone has not yet completed E2E acceptance against PRD §6.)

### Active

<!-- Current scope. Building toward these. Detail in REQUIREMENTS.md (v1 PoC + v1.1 Overhaul). -->

**Foundation (PoC v1):**
- [ ] **Ingress:** Secure GMeT webhook endpoint that parses CAP v1.2 payloads and triggers the auto-dispatch path within the 5s budget (REQ-gmet-webhook-endpoint, REQ-gmet-webhook-auth, REQ-cap-payload-parsing)
- [ ] **Dispatch:** MNO webhook push with retry, plus SMS to pre-registered test numbers (REQ-mno-webhook-dispatch, REQ-sms-dispatch)
- [ ] **Enrichment:** Geo-resolution to Ghanaian regions/districts, English to Twi/Hausa translation with native-quality voices, TTS audio links (REQ-geo-resolution, REQ-translation, REQ-tts)
- [ ] **Persistence:** All pipeline events logged in MongoDB for audit / after-action analysis (REQ-event-logging)

**Build / Logic / Critical Secrets (Phase 1):**
- [ ] **Build/infra hygiene:** Procfile/Dockerfile/.dockerignore/requirements.txt corrected (REQ-build-infra-hygiene)
- [ ] **GMeT auto-dispatch:** webhook bypasses validator gate to meet PRD §6 acceptance #5 (REQ-fix-workflow-stage-gate)
- [ ] **Manual entry robustness:** lat/lon empty-string crash fixed (REQ-fix-latlon-empty-string)
- [ ] **Validator efficiency:** find_one instead of full scan (REQ-fix-validator-scan)
- [ ] **Critical secrets to env:** SECRET_KEY + webhook API key moved to env vars preserving current values (REQ-env-var-secrets)

**Security Hardening + Real 2FA (Phase 2):**
- [ ] **Real 2FA:** Africa's Talking SMS replaces email-+-stdout-code (REQ-real-2fa-africastalking)
- [ ] **Hardening:** rate limiting, CSRF, secure cookies, CORS lockdown, crypto RNG, IP gate cleanup, dashboard secret-leakage removal, full secret rotation (REQ-rate-limiting, REQ-csrf, REQ-secure-session, REQ-cors-lockdown, REQ-cryptographic-rng, REQ-tighten-allowed-ips, REQ-remove-dashboard-secret-leakage, REQ-secret-rotation)

**Enrichment Quality (Phase 3):**
- [ ] **Real translations / TTS:** fix malformed `OPENAI_API_KEY` value, batch translation calls, native-quality voices for Twi/Hausa via Khaya / Google TTS (REQ-fix-malformed-env-key, REQ-translation-batching, REQ-tts-language-quality)

**Frontend Migration (Phase 4):**
- [ ] **React + Vite + TypeScript + Tailwind + framer-motion** SPA replaces vanilla JS + Jinja dashboard; light/dark theme ported; Webhook Config + Test Dispatcher screens delivered (REQ-react-vite-frontend, REQ-flask-json-api-only, REQ-tailwind-glassmorphic-system, REQ-framer-motion-transitions, REQ-port-light-dark, REQ-dashboard-active-alerts-view, REQ-dashboard-webhook-config, REQ-dashboard-test-dispatcher, REQ-design-language-glassmorphism)

**Map UX (Phase 5):**
- [ ] **Mapbox globe + region/district + NL geocoding + flyTo + rain overlay:** "heavy rain expected at Osu in Accra" → map flies to Osu with rain animation (REQ-globe-mapbox, REQ-ghana-admin-geojson-districts, REQ-region-district-selectors, REQ-natural-language-location, REQ-map-flyto-zoom, REQ-rain-animation-overlay)

**AI Advisory Agent (Phase 6):**
- [ ] **Claude Sonnet 4.6 with tool use:** populates CAP draft from natural language for human review/edit (REQ-ai-advisory-agent, REQ-natural-language-cap-draft, REQ-tool-geocode, REQ-tool-population, REQ-tool-historical, REQ-tool-severity, REQ-tool-draft-advisory, REQ-prompt-caching)

**Globe + UI Polish + Pipeline Detail Surfaces (Phase 7):**
- [ ] **react-globe.gl** anchored at Ghana cities matching the reference screenshot; framer-motion transitions; pipeline detail shows translations + per-language audio + dispatch status (REQ-globe-anchored-arcs, REQ-globe-aesthetic-match, REQ-pipeline-detail-translations, REQ-pipeline-detail-audio-players, REQ-pipeline-detail-dispatch-status, REQ-framer-motion-polish)

**Public Display Endpoint (Phase 8):**
- [ ] **`/public/feed/display`** TV-style page + `/public/feed/receive` MNO sink + `/live_feed` Socket.IO namespace; default `MNO_WEBHOOK_URL` loops back locally for testing (REQ-public-mno-receiver, REQ-public-display-page, REQ-public-socketio-namespace, REQ-mno-webhook-default-loops-back, REQ-public-rate-limit)

**Tests + Visual Regression (Phase 9):**
- [ ] **pytest + Playwright via webapp-testing skill:** unit + integration + E2E + screenshot regression (REQ-tests-unit-integration, REQ-tests-playwright-e2e, REQ-tests-visual-regression)

### Out of Scope

<!-- Explicit boundaries. Includes reasoning to prevent re-adding. -->

- **Cell broadcast, TV/radio override, satellite, IoT sensor ingress, social media, digital signage, HF/VHF radio fallback, IVR** — These are E-CoP SPEC FR3.1 / FR7.x / FR8.x / FR9.x channels deferred to Milestone 2+; current milestone validates only MNO webhook + SMS + public TV-display feed.
- **Multi-stakeholder portals (NGOs, Police/Fire, UN/ITU, public-facing apps)** — SPEC §2 stakeholder classes 2, 4, 5, 6 are deferred; current milestone serves NCA / GMeT / NADMO operator roles only.
- **Sign-language overlays, screen-reader support beyond browser defaults** — SPEC NFR11 accessibility deferred to a future milestone.
- **Backwards compatibility with analog HF / trunk radio** — SPEC §3.3 system constraint deferred (no HF/VHF dispatch channel).
- **1000 concurrent users (SPEC NFR2), millions/min throughput (SPEC NFR5), 99.9% availability (SPEC NFR3), redundant active-active (NFR4)** — NFR scale targets apply to full E-CoP rollout; current milestone validates pipeline correctness, not nationwide load.
- **End-to-end encryption for first responders (SPEC NFR7)** — No first-responder channel in current milestone.
- **Real radar feed for the rain animation overlay** — Phase 5's overlay is an animated CSS/WebGL effect triggered by event keywords, not data-driven from radar. A radar-data-backed version is a future enhancement.
- **Postgres analytics insert beyond a documented stub** — `external_analytics_service.py:43` TODO is deferred unless it falls naturally out of Phase 1's logic-bug sweep.

**Note:** Items previously listed as out-of-scope under the original PoC roadmap (real 2FA, AI advisory agent, public display, frontend framework migration, automated tests) have been **moved to Active** as of the 2026-05-09 overhaul scope absorption (after `/ultraplan` cloud session failed). They are now tracked across Phases 2-9.

## Context

- **Active entry point** is `ghana_cap_app.py`, NOT `app.py` (the latter has been deleted in the working tree; `app[DEPRECATED].py` is reference-only). `Procfile` and `Dockerfile` still reference `app:app` — stale and must be updated when deploying.
- **Pipeline funnel:** `ghana_cap_app.process_alert_logic` is the single entry point for all alert ingress (GMeT webhook + manual form) — generates identifier, geo-resolves, translates+TTS, persists, conditionally dispatches, then emits Socket.IO `new_alert` and pushes to external analytics.
- **Workflow state machine** (`workflow_stage`): 0 = Rejected/Draft, 1 = Pending Validation (default for `cap generator` submissions), 3 = Dispatched. Currently `process_alert_logic` only dispatches when `workflow_stage == 3`. **This conflicts with PRD §6 acceptance #5** which requires GMeT-originated alerts to auto-dispatch within 5s — see Phase 1 in ROADMAP.md.
- **Graceful-degradation invariant:** every external integration in `services/` (OpenAI, Twilio, SMTP, MNO webhook) checks for credentials on init and falls back to mock/log behavior when absent. The app boots and the workflow runs end-to-end with zero external creds. This is an architectural property to preserve.
- **Persistence split:** MongoDB Atlas (`fsrp_aggregator` DB) is the operational store (alerts/users/verification_codes); PostgreSQL (`earlywarningdb.sql`) is an *external* analytics DB owned by another team — the platform pushes via `external_analytics_service.sync_alert` (currently logs only; psycopg2 insert is a TODO at line 43).
- **Frontend:** Server-rendered Jinja with vanilla JS, Leaflet, and Socket.IO. Active templates are `ghana_cap_dashboard.html` and `login.html`; everything else in `templates/` is historical.
- **Tech debt flagged in CLAUDE.md:** GMeT webhook API key check at `ghana_cap_app.py:114` is the literal string `"gh_cap_poc_key_2026"`; `app.config['SECRET_KEY']` is also hard-coded. Both must move to env vars before non-PoC deployment, but **don't change them silently** — they break the existing GMeT webhook contract and invalidate active sessions.
- **PRD vs SPEC scope hierarchy:** SPEC ("Unified E-CoP", RQ_DOC_0) is the parent program; PRD.txt is the GMeT E2E PoC milestone within it. Treat all SPEC-only requirements (cell broadcast, TV/radio, satellite, IoT, social media, public portals) as future-milestone scope, not current.

## Constraints

- **Tech stack (implicit, current-state confirmed):** Python/Flask + eventlet Socket.IO, MongoDB Atlas operational store, OpenAI (gpt-4o-mini for translation, tts-1 for TTS), Twilio for SMS. — Source: PRD §5, CLAUDE.md.
- **Protocol:** CAP v1.2 is the canonical alert format (PRD §2, SPEC NFR14). Outbound MNO payload and inbound GMeT payload both must conform.
- **Latency:** PRD §6 acceptance #5 — MNO webhook endpoint receives the fully enriched JSON payload **within 5 seconds** of the initial GMeT trigger. SPEC NFR1 — high-priority alerts broadcast within 1 minute of approval (PoC tightens this to 5s for the auto-dispatch path).
- **Languages:** Minimum viable PoC is English + Twi + Hausa (PRD §6 acceptance #3). Ga and Ewe are mentioned in PRD §2 step 4 as future targets but not required for PoC acceptance.
- **Auth scheme:** Email + 6-digit code via SMTP (or stdout in dev) — intentionally minimal for PoC. Real 2FA is out of scope here.
- **Deployment target:** `Procfile` and `Dockerfile` reference the deleted `app.py` and must be updated to `ghana_cap_app:app` before any non-dev deploy. **Do not** revert the rename.
- **Hard-coded values that cannot be silently changed:** GMeT webhook API key string `"gh_cap_poc_key_2026"` (active contract with GMeT); `app.config['SECRET_KEY']` (active session invalidation risk).
- **External dependency:** Downstream analytics PostgreSQL schema is owned by another team — mapping lives in `external_analytics_service._map_agency_id`; do not run `earlywarningdb.sql` against the project's own DB.
- **File size convention (inherited from GEMINI.md):** Keep files under ~300–400 lines; refactor at that point.
- **No mock data in dev/prod paths** — mocks are acceptable only as graceful fallbacks when an external credential is missing (the existing pattern across `services/`). Do not seed fake alerts.
- **Never overwrite `.env`** without explicit confirmation.

## Key Decisions

<!-- Decisions that constrain future work. The following are *implicit* technical commitments
extracted from SPEC + PRD + CLAUDE.md during ingest. They are NOT yet locked ADRs — promote
to locked via /gsd-decision when ready. Source intel: .planning/intel/decisions.md. -->

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| **IMPLICIT-001** — CAP v1.2 as canonical alert format | Both SPEC NFR14 and PRD §2 mandate CAP v1.2 for interoperability with telecom operators | — Pending (proposed, not locked) |
| **IMPLICIT-002** — Python/Flask + eventlet Socket.IO backend | PRD §5 specifies Python/Flask; current code confirms eventlet for Socket.IO real-time | — Pending (proposed, not locked) |
| **IMPLICIT-003** — MongoDB Atlas as operational store (`fsrp_aggregator` DB) | PRD §5 specifies MongoDB; SPEC leaves DB choice unspecified. Collections: `users`, `verification_codes`, `alerts` | — Pending (proposed, not locked) |
| **IMPLICIT-004** — External PostgreSQL analytics DB owned by another team | Inherited operational constraint; not in SPEC or PRD. Mapping in `external_analytics_service` | — Pending (treat as dependency, not design choice) |
| **IMPLICIT-005** — Glassmorphism UI design language | PRD §4 prescribes glassmorphism; CLAUDE.md confirms in-use across active templates | — Pending (proposed, not locked) |
| **IMPLICIT-006** — Workflow-stage state machine (0 / 1 / 3) | Encoded in `process_alert_logic` line 241 dispatch gate. **NOT in PRD or SPEC** — emerged from implementation. Conflicts with PRD §6 acceptance #5 (auto-dispatch within 5s of GMeT trigger). Phase 1 resolves this conflict | ⚠️ Revisit (PRD takes precedence; current code requires change) |
| **IMPLICIT-007** — Graceful-degradation pattern for external integrations | All `services/` modules check for creds on init and fall back to mock/log behavior. App boots end-to-end with zero external creds | — Pending (architectural invariant; preserve) |

---
*Last updated: 2026-05-09 after ingest synthesis (3 docs: SPEC RQ_DOC_0, PRD.txt, CLAUDE.md; 0 ADRs locked, 7 implicit decisions extracted)*
