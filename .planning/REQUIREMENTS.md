# Requirements: Ghana National CAP Platform

**Defined:** 2026-05-09 (initial PoC scope)
**Expanded:** 2026-05-09 (overhaul scope absorbed locally after `/ultraplan` failed)

**Core Value:** A national emergency nexus that auto-dispatches GMeT alerts within 5 seconds, lets operators draft alerts in natural language with AI assistance, dispatches to telecom + public-display channels, and is hardened for production with real 2FA + automated tests.

**Source intel (PoC v1):** `.planning/intel/requirements.md` (PRD.txt) — IDs preserved verbatim.
**Source intent (Overhaul v1.1):** user `/ultraplan` ask 2026-05-09 — see PROJECT.md "Active" requirements and ROADMAP.md phases 1-10.

---

## v1 Requirements (PRD PoC scope)

Original PoC requirements from PRD.txt. Each maps to one or more phases below.

### Ingress

- [ ] **REQ-gmet-webhook-endpoint**: Expose a secure POST endpoint at `/api/v1/alerts/gmet/webhook` for GMeT webhook ingress (PRD §3.1, §6 acceptance #1) — Phase 1
- [ ] **REQ-gmet-webhook-auth**: Authenticate GMeT webhook calls via API key OR Bearer token validation (PRD §3.1) — Phase 1, hardened in Phase 2
- [ ] **REQ-cap-payload-parsing**: Parse incoming CAP v1.2 payload — extract `identifier`, `sender`, `sent`, `status`, `msgType`, `scope`, `info` (category, event, urgency, severity, certainty, headline, description, area), validate against CAP v1.2, map to internal data structures (PRD §3.1, §2 step 2) — Phase 1

### Dispatch

- [ ] **REQ-mno-webhook-dispatch**: Push fully enriched JSON payload (text, geo-data, media links) to configured MNO endpoint with exponential-backoff retry; **MNO endpoint must receive the payload within 5 seconds of the initial GMeT trigger** (PRD §3.3, §2 step 6 Target A, §6 acceptance #5) — Phase 1
- [ ] **REQ-sms-dispatch**: Send concise text-only SMS (highest-priority translated text, default English) to pre-registered test phone numbers mapped from administrative areas (PRD §3.3, §2 step 6 Target B, §6 acceptance #6) — Phase 1

### Enrichment

- [ ] **REQ-geo-resolution**: Resolve incoming coordinates / GeoJSON polygons / circles / manual graphical polygons to Ghanaian administrative areas; output array of localized strings (e.g., `["Greater Accra Region", "Accra Metropolitan"]`) (PRD §3.2, §6 acceptance #2) — Phase 3
- [ ] **REQ-translation**: Translate the English alert text into local language variants — minimum viable PoC: English + Twi + Hausa (PRD §3.2, §6 acceptance #3) — Phase 3
- [ ] **REQ-tts**: Convert translated and English text into MP3/WAV audio files with accessible URLs (cloud bucket OR local temporary storage) (PRD §3.2, §6 acceptance #4) — Phase 3

### Persistence & Observability

- [ ] **REQ-event-logging**: Persist all pipeline events to MongoDB for audit / after-action analysis (PRD §6 acceptance #7) — Phase 10

### Admin Dashboard (UI) — implemented under React in Phase 4

- [ ] **REQ-dashboard-active-alerts-view**: Provide an alert lifecycle view (Kanban-style or list view) showing pipeline statuses Received → Processing → Translated → Dispatched (PRD §4) — Phase 4
- [x] **REQ-dashboard-webhook-config**: Allow operators to generate and manage the GMeT webhook URL and API keys via dashboard screens (PRD §4) — Phase 4
- [x] **REQ-dashboard-test-dispatcher**: Manual trigger button injects a mock GMeT JSON payload to test the full flow without waiting for a real weather event (PRD §4) — Phase 4
- [ ] **REQ-design-language-glassmorphism**: Adhere to glassmorphism design language across the dashboard — semi-transparent backgrounds with background blur, subtle light borders, distinct drop shadows, layered modern aesthetic over a clean dark-mode-friendly background (PRD §4) — Phase 4

---

## v1.1 Requirements (Overhaul scope, added 2026-05-09)

Absorbed from the user's `/ultraplan` brief after the cloud planner failed. Each maps to a phase in the expanded ROADMAP.md.

### Build / Infra Hygiene (Phase 1)

- [ ] **REQ-build-infra-hygiene**: Procfile and Dockerfile reference `ghana_cap_app:app` (not `app:app`); `.dockerignore` excludes `.env`, `*.zip`, `*.pdf`, screenshots, `.venv/`, `.git/`, `.planning/`; `requirements.txt` includes `africastalking`, `flask-limiter`, `flask-wtf`, `anthropic`, `python-dotenv`, `psycopg2-binary` (for the analytics TODO).
- [ ] **REQ-fix-workflow-stage-gate**: GMeT webhook auto-dispatches (`workflow_stage=3`) so PRD §6 acceptance #5 (≤5s dispatch) holds. Manual generator submissions still go to stage 1 (validator gate). Resolves INGEST-CONFLICTS.md INFO #3.
- [ ] **REQ-fix-latlon-empty-string**: `process_alert_logic` does not crash on empty-string lat/lon (manual form ships empty hidden inputs until map is clicked). Either tolerate empty strings with default coords or require map click before submit.
- [ ] **REQ-fix-validator-scan**: `validate_alert` uses `db.find_alert_by_identifier` (find_one) instead of full collection scan via `get_all_alerts()`.
- [ ] **REQ-env-var-secrets**: `SECRET_KEY` and GMeT webhook API key are read from env vars; `.env.example` documents all required and optional vars; preserves current literal values for the active GMeT contract and active sessions.

### Security Hardening + Real 2FA (Phase 2)

- [ ] **REQ-real-2fa-africastalking**: Login uses Africa's Talking SMS to deliver the verification code; falls back to logging the code when AT credentials are absent. Twilio remains as a fallback adapter.
- [ ] **REQ-rate-limiting**: Flask-Limiter applied to `/login` (per-IP); lockout after N failed verification attempts.
- [ ] **REQ-csrf**: Flask-WTF CSRF protection on state-changing routes; JSON endpoints use a token mechanism that survives Socket.IO usage.
- [ ] **REQ-secure-session**: Session cookies are `Secure`, `HttpOnly`, `SameSite=Lax` (or `Strict` where appropriate).
- [ ] **REQ-cors-lockdown**: Socket.IO `cors_allowed_origins` restricted to known origins via env var; not `"*"`.
- [ ] **REQ-cryptographic-rng**: Verification code uses `secrets.randbelow(900000) + 100000`, not `random.randint`.
- [ ] **REQ-tighten-allowed-ips**: Three of four seed users no longer have `allowed_ips: ["*"]`; gate is either tightened or removed in favor of proper auth.
- [ ] **REQ-remove-dashboard-secret-leakage**: Dashboard Settings tab no longer prints the GMeT webhook key (was at `templates/ghana_cap_dashboard.html:513`) or Twilio SID (was at `:518`).
- [ ] **REQ-secret-rotation**: All previously-leaked credentials (MongoDB password, OpenAI key, Twilio token) documented as rotated; current values live only in `.env` with placeholders in `.env.example`.

### Enrichment Quality (Phase 3)

- [ ] **REQ-fix-malformed-env-key**: `OPENAI_API_KEY` value in `.env` is a bare key (currently malformed as `OpenAI(api_key="…")` literal — silently mocks all translations and TTS). Fix unblocks v1 REQ-translation and REQ-tts.
- [ ] **REQ-translation-batching**: Translation makes a single OpenAI call returning a structured JSON object with all target languages, not N+1 sequential roundtrips.
- [ ] **REQ-tts-language-quality**: Twi (and v2 Ga / Ewe) speak in native voices via Ghana NLP Khaya TTS; Hausa via Google Cloud TTS or Khaya; English via OpenAI / ElevenLabs. No more English-pronounced phonetics from `voice="alloy"` for African languages.

### Frontend Migration (Phase 4)

- [x] **REQ-react-vite-frontend**: Operator dashboard is a React + Vite + TypeScript SPA built into `frontend/dist/`, served by Flask (or split origins).
- [x] **REQ-flask-json-api-only**: Flask state-changing routes return JSON only; HTML rendering is delegated to React (Jinja remains for `/login` only, or that's also migrated).
- [x] **REQ-tailwind-glassmorphic-system**: Tailwind CSS + a glassmorphic component library (e.g. custom CSS layer) replaces the inline CSS variables — semi-transparent backgrounds, backdrop-blur, layered shadows.
- [ ] **REQ-framer-motion-transitions**: Tab transitions and alert-card expand/collapse use framer-motion with smooth, fluid timing.
- [ ] **REQ-port-light-dark**: The existing light/dark theme toggle (currently at `ghana_cap_dashboard.html:533-540`) is ported to a React-friendly equivalent (e.g. `next-themes` pattern). Don't rebuild — port behavior.

### Map UX (Phase 5)

- [ ] **REQ-globe-mapbox**: Mapbox GL JS globe (MapLibre fallback for tokenless dev) replaces Leaflet for the Manual Entry tab map.
- [ ] **REQ-ghana-admin-geojson-districts**: Add Ghana admin-2 (district) GeoJSON to `static/`; the existing `static/ghana_regions.json` is admin-1 only.
- [ ] **REQ-region-district-selectors**: Region dropdown (16 regions from `static/ghana_regions.json`) → district dropdown (cascading).
- [ ] **REQ-natural-language-location**: Free-form text input ("Osu in Accra") resolves to lat/lon via Mapbox Geocoding API biased to Ghana (Nominatim fallback); on resolve, the map performs `flyTo` with smooth animation.
- [ ] **REQ-map-flyto-zoom**: Map smoothly flies to the resolved coordinates with appropriate zoom level for the location's specificity (city-level for "Accra", neighborhood-level for "Osu").
- [ ] **REQ-rain-animation-overlay**: When category=Met and event matches /rain|storm|flood/i, an animation overlay activates over the affected area in real time during CAP creation. Variants: rain (default), storm, flood.

### AI Advisory Agent (Phase 6)

- [ ] **REQ-ai-advisory-agent**: Anthropic Claude Sonnet 4.6 integrated via the SDK with tool use; system prompt + Ghana admin reference data cached via prompt caching for cost.
- [ ] **REQ-natural-language-cap-draft**: A "Draft from natural language" button on Manual Entry calls `/api/v1/agents/draft` which runs the agent and returns a structured CAP JSON for human review/edit.
- [ ] **REQ-tool-geocode**: Agent tool `geocode_ghana_location(text)` resolves Ghanaian place names to lat/lon + region + district.
- [ ] **REQ-tool-population**: Agent tool `lookup_population_density(region, district)` returns population density data (Ghana Statistical Service).
- [ ] **REQ-tool-historical**: Agent tool `query_historical_alerts(region, event_type)` queries the MongoDB `alerts` collection for historical context.
- [ ] **REQ-tool-severity**: Agent tool `assess_emergency_severity(event_type, area_population, time_of_year)` returns suggested CAP severity/urgency/certainty.
- [ ] **REQ-tool-draft-advisory**: Agent tool `draft_cap_advisory(event_type, severity, area, language="en")` returns CAP-conformant headline + description + instruction strings.
- [ ] **REQ-prompt-caching**: System prompt + Ghana admin reference data cached via Anthropic prompt caching (`cache_control: ephemeral`) on every agent invocation for cost efficiency.

### Globe + UI Polish (Phase 7)

- [ ] **REQ-globe-anchored-arcs**: `react-globe.gl` background renders a dark globe with great-circle arcs anchored at named Ghana cities (Accra, Kumasi, Tamale, Sekondi-Takoradi, Cape Coast, Tema, Ho, Wa, Bolgatanga, Sunyani) plus neighbor capitals (Lomé, Abidjan, Ouagadougou, Niamey, Lagos).
- [ ] **REQ-globe-aesthetic-match**: Visual comparison against `Screenshot 2026-05-08 141301.png` confirms the dark + cyan/teal arc + city-anchored aesthetic.
- [ ] **REQ-pipeline-detail-translations**: Pipeline tab alert detail shows English / Twi / Hausa translation tabs (or stacked sections), each with its full translated text.
- [ ] **REQ-pipeline-detail-audio-players**: Each translation has an embedded `<audio>` player loaded from `audio_links[lang]`; a status badge indicates audio file existence (HEAD request to `/static/audio/<file>`).
- [ ] **REQ-pipeline-detail-dispatch-status**: Detail panel shows MNO HTTP status (or "Not dispatched"), SMS provider IDs (or "Failed/Mocked"), and public-feed broadcast confirmation (or "Pending").
- [ ] **REQ-framer-motion-polish**: Alert-state transitions (Received → Processing → Translated → Dispatched) animate with framer-motion; tab switches use framer-motion `AnimatePresence`.

### Public Display Endpoint (Phase 8)

- [ ] **REQ-public-mno-receiver**: `POST /public/feed/receive` accepts dispatched JSON from `dispatch_service.dispatch_to_mno`, persists in memory or MongoDB `public_feed` collection, broadcasts on `/live_feed` Socket.IO namespace.
- [ ] **REQ-public-display-page**: `GET /public/feed/display` renders a full-screen TV-display page (revives/replaces `templates/tv_display.html`) showing the latest alert with map zoom + audio playback + headline + animation.
- [ ] **REQ-public-socketio-namespace**: `/live_feed` namespace (currently referenced by `data_receiver.py` but never emitted to from `ghana_cap_app.py`) is wired to `dispatch_service.dispatch_to_mno`.
- [ ] **REQ-mno-webhook-default-loops-back**: `MNO_WEBHOOK_URL` env var defaults to the local `/public/feed/receive` endpoint when unset, closing the dispatch loop locally for testing.
- [ ] **REQ-public-rate-limit**: Per-IP rate limit on `/public/feed/display`; optional signed viewer token query param (`?viewer=<jwt>`) for embedded screens to bypass.

### Tests + Visual Regression (Phase 9)

- [ ] **REQ-tests-unit-integration**: pytest covers services (mocked external APIs) and endpoint flows (Flask test client); covers all REQ-* implementations from Phases 1-8.
- [ ] **REQ-tests-playwright-e2e**: Playwright (via the `webapp-testing` skill) covers login (real AT sandbox SMS), manual entry with AI agent, validator approval, public feed broadcast.
- [ ] **REQ-tests-visual-regression**: Screenshot regression captures key states: dark dashboard, light dashboard, alert detail expanded with audio players, map flyTo zoomed to Osu with rain overlay, globe loaded with arcs, public display rendering an alert.

### Acceptance (Phase 10)

(No new REQ-* IDs — Phase 10 reconfirms all prior phase success criteria end-to-end.)

---

## v2 Requirements (Deferred to Milestone 2+)

Tracked but not in current roadmap. Source: SPEC `.planning/intel/constraints.md` plus PRD §2 step 4 extras.

### Additional Languages

- **REQ-translation-ga**: Add Ga as a translation target language (PRD §2 step 4 — non-blocking for PoC)
- **REQ-translation-ewe**: Add Ewe as a translation target language (PRD §2 step 4 — non-blocking for PoC)

### Multi-Channel Dispatch (SPEC FR3.1)

- **REQ-cell-broadcast**, **REQ-tv-radio-override**, **REQ-social-media**, **REQ-digital-signage**

### Resilience & Reach (SPEC FR7-FR9)

- **REQ-hf-vhf-radio**, **REQ-iot-sensors**, **REQ-satellite-comm**

### Two-Way & Coordination (SPEC FR4-FR6)

- **REQ-ack-tracking**, **REQ-multi-agency-portal**, **REQ-collab-channels**

### Governance & Reporting (SPEC FR12-FR13)

- **REQ-rbac-formal**, **REQ-audit-logs**, **REQ-realtime-dashboards**, **REQ-after-action-reports**

### Public Engagement (SPEC FR10-FR11)

- **REQ-scheduled-education**, **REQ-public-feedback**

---

## Out of Scope (M1 + likely M2)

| Feature | Reason |
|---------|--------|
| Sign-language overlays, full a11y per SPEC NFR11 | Deferred to a future a11y milestone |
| Backwards compatibility with analog HF / trunk radio (SPEC §3.3) | Deferred to a later resilience milestone |
| 1000 concurrent users (SPEC NFR2), millions/min throughput (SPEC NFR5), 99.9% availability (SPEC NFR3), redundant active-active (NFR4) | NFR scale targets apply to full E-CoP; current milestone validates pipeline correctness, not nationwide load |
| End-to-end encryption for first responders (SPEC NFR7) | No first-responder channel in current milestone |
| Multi-stakeholder portals (Police/Fire, NGOs, UN/ITU, public app) | SPEC §2 stakeholder classes 2, 4, 5, 6 deferred |

---

## Traceability

Which phases cover which requirements.

### v1 (PoC)

| Requirement | Phase | Status |
|-------------|-------|--------|
| REQ-gmet-webhook-endpoint | Phase 1 | Pending |
| REQ-gmet-webhook-auth | Phase 1 (hardened in Phase 2) | Pending |
| REQ-cap-payload-parsing | Phase 1 | Pending |
| REQ-mno-webhook-dispatch | Phase 1 | Pending |
| REQ-sms-dispatch | Phase 1 | Pending |
| REQ-geo-resolution | Phase 3 | Pending |
| REQ-translation | Phase 3 | Pending |
| REQ-tts | Phase 3 | Pending |
| REQ-dashboard-active-alerts-view | Phase 4 | Pending |
| REQ-dashboard-webhook-config | Phase 4 | Complete |
| REQ-dashboard-test-dispatcher | Phase 4 | Complete |
| REQ-design-language-glassmorphism | Phase 4 | Pending |
| REQ-event-logging | Phase 10 | Pending |

### v1.1 (Overhaul)

| Requirement | Phase | Status |
|-------------|-------|--------|
| REQ-build-infra-hygiene | Phase 1 | Pending |
| REQ-fix-workflow-stage-gate | Phase 1 | Pending |
| REQ-fix-latlon-empty-string | Phase 1 | Pending |
| REQ-fix-validator-scan | Phase 1 | Pending |
| REQ-env-var-secrets | Phase 1 | Pending |
| REQ-real-2fa-africastalking | Phase 2 | Pending |
| REQ-rate-limiting | Phase 2 | Pending |
| REQ-csrf | Phase 2 | Pending |
| REQ-secure-session | Phase 2 | Pending |
| REQ-cors-lockdown | Phase 2 | Pending |
| REQ-cryptographic-rng | Phase 2 | Pending |
| REQ-tighten-allowed-ips | Phase 2 | Pending |
| REQ-remove-dashboard-secret-leakage | Phase 2 | Pending |
| REQ-secret-rotation | Phase 2 | Pending |
| REQ-fix-malformed-env-key | Phase 3 | Pending |
| REQ-translation-batching | Phase 3 | Pending |
| REQ-tts-language-quality | Phase 3 | Pending |
| REQ-react-vite-frontend | Phase 4 | Complete |
| REQ-flask-json-api-only | Phase 4 | Complete |
| REQ-tailwind-glassmorphic-system | Phase 4 | Complete |
| REQ-framer-motion-transitions | Phase 4 | Pending |
| REQ-port-light-dark | Phase 4 | Pending |
| REQ-globe-mapbox | Phase 5 | Pending |
| REQ-ghana-admin-geojson-districts | Phase 5 | Pending |
| REQ-region-district-selectors | Phase 5 | Pending |
| REQ-natural-language-location | Phase 5 | Pending |
| REQ-map-flyto-zoom | Phase 5 | Pending |
| REQ-rain-animation-overlay | Phase 5 | Pending |
| REQ-ai-advisory-agent | Phase 6 | Pending |
| REQ-natural-language-cap-draft | Phase 6 | Pending |
| REQ-tool-geocode | Phase 6 | Pending |
| REQ-tool-population | Phase 6 | Pending |
| REQ-tool-historical | Phase 6 | Pending |
| REQ-tool-severity | Phase 6 | Pending |
| REQ-tool-draft-advisory | Phase 6 | Pending |
| REQ-prompt-caching | Phase 6 | Pending |
| REQ-globe-anchored-arcs | Phase 7 | Pending |
| REQ-globe-aesthetic-match | Phase 7 | Pending |
| REQ-pipeline-detail-translations | Phase 7 | Pending |
| REQ-pipeline-detail-audio-players | Phase 7 | Pending |
| REQ-pipeline-detail-dispatch-status | Phase 7 | Pending |
| REQ-framer-motion-polish | Phase 7 | Pending |
| REQ-public-mno-receiver | Phase 8 | Pending |
| REQ-public-display-page | Phase 8 | Pending |
| REQ-public-socketio-namespace | Phase 8 | Pending |
| REQ-mno-webhook-default-loops-back | Phase 8 | Pending |
| REQ-public-rate-limit | Phase 8 | Pending |
| REQ-tests-unit-integration | Phase 9 | Pending |
| REQ-tests-playwright-e2e | Phase 9 | Pending |
| REQ-tests-visual-regression | Phase 9 | Pending |

**Coverage:**
- v1 requirements: 13 (all mapped)
- v1.1 requirements: 49 (all mapped)
- Total active: 62 (all mapped to phases 1-10)

---
*Requirements defined: 2026-05-09*
*Overhaul scope absorbed: 2026-05-09 (after /ultraplan cloud session failed)*
