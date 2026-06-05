# Roadmap: Ghana National CAP Platform

## Overview

This roadmap covers **Milestone 1 — National Emergency Nexus**, expanded on 2026-05-09 from the original GMeT E2E PoC scope to absorb the full overhaul scope from the user's `/ultraplan` ask (real 2FA via Africa's Talking, AI advisory agent, frontend migration to React + Vite, Mapbox-based map UX with natural-language geocoding and rain animation overlay, react-globe.gl revamp, public TV-display endpoint, automated tests). Ten phases. The journey takes the platform from its current state (working pipeline gated behind validator approval, malformed `OPENAI_API_KEY` silently mocking translations/TTS, hardcoded secrets, stale deploy artifacts, vanilla JS frontend) to a hardened national emergency nexus that:

- Auto-dispatches GMeT webhooks within 5 seconds (PRD §6 acceptance #5)
- Authenticates operators via real Africa's Talking SMS 2FA
- Lets operators draft alerts in natural language (e.g. "heavy rain expected at Osu in Accra") and an AI agent fills in CAP fields, geocodes, and animates a rain overlay on a Mapbox globe centered on the named area
- Renders the operator dashboard in React + Tailwind + framer-motion with a `react-globe.gl` background showing arcs anchored to Ghana cities
- Surfaces translations + per-language audio players + dispatch status in the pipeline detail
- Broadcasts dispatched alerts to a public TV-display URL for downstream consumers
- Has pytest + Playwright tests covering the full flow

The broader Unified E-CoP scope (cell broadcast, satellite, IoT, multi-agency portal, public feedback, full a11y) remains deferred to Milestone 2+ and is tracked in REQUIREMENTS.md v2 / PROJECT.md "Out of Scope."

## Milestones

- 🚧 **Milestone 1 — National Emergency Nexus** — Phases 1-10 (in progress, 2026-05-09)
- 📋 **Milestone 2+ (Unified E-CoP scale-out)** — not yet planned (see REQUIREMENTS.md v2 / SPEC constraints)

## Phases

**Phase Numbering:**
- Integer phases (1, 2, …, 10): Planned milestone work
- Decimal phases (e.g., 2.1): Reserved for urgent insertions via `/gsd-insert-phase`

**Sequencing principle:** infra → security → enrichment quality → frontend → map → AI → polish → public surface → tests → acceptance. The user's stated execution order ("first fix Procfile/Dockerfile, then logical issues, then security…") is preserved.

- [ ] **Phase 1: Build/Infra Hygiene + Logic Bug Sweep + Critical Secrets to Env** — Procfile/Dockerfile rename, .dockerignore expansion, requirements.txt updates, fix `workflow_stage` gate for GMeT auto-dispatch, fix lat/lon empty-string crash, replace validator full-scan with find_one, move SECRET_KEY + GMeT webhook API key to env vars (preserving current values), add `.env.example`.
- [ ] **Phase 2: Security Hardening + Real-API 2FA via Africa's Talking** — env-var all remaining secrets (Mongo, Twilio SID), rotate leaked credentials, switch verification code to `secrets.randbelow`, add Flask-Limiter rate limiting on /login, add Flask-WTF CSRF on state-changing routes, lock down Socket.IO `cors_allowed_origins`, secure session cookies (Secure, HttpOnly, SameSite), tighten `allowed_ips` for seed users, remove dashboard secret leakage at template lines 513/518, integrate Africa's Talking SMS 2FA with sandbox tests.
- [ ] **Phase 3: Enrichment Quality Upgrade** — fix malformed `OPENAI_API_KEY` value in `.env` (currently `OpenAI(api_key="…")` literal — silently mocks translations/TTS), batch translation into a single OpenAI call returning a structured JSON dict, switch Twi/Ga/Ewe TTS from OpenAI alloy to Ghana NLP Khaya, switch Hausa to Google Cloud TTS or Khaya, keep English on OpenAI/ElevenLabs, preserve graceful-degradation for all paths.
- [x] **Phase 4: Frontend Migration to React + Vite + TypeScript + Tailwind + framer-motion** — scaffold Vite project under `frontend/`, configure Flask to serve the build (or split origins), port glassmorphic CSS-variable system to a Tailwind component layer, port light/dark theme toggle (already exists in Jinja — port behavior, not rebuild), implement Pipeline tab + Manual Entry tab + Settings tab + Webhook Config + Test Dispatcher screens; Flask becomes pure JSON API. **Completed 2026-05-09; all 7 ROADMAP §90 success criteria verified autonomously via Playwright (tests/e2e_smoke.py, 20/20 PASS).**
- [ ] **Phase 5: Map UX — Mapbox Globe, Region/District Selectors, NL Geocoding, flyTo, Rain Animation Overlay** — replace Leaflet with Mapbox GL JS (MapLibre fallback for tokenless dev), wire region/district dropdowns to Ghana admin GeoJSON (need district-level GeoJSON, not just regions), add a natural-language location input that triggers `flyTo` on resolved coords, build a rain animation layer that activates when category=Met and event matches /rain|storm|flood/i.
- [ ] **Phase 6: AI Advisory Agent — Claude Sonnet 4.6 with Tool Use + Structured CAP JSON** — Anthropic SDK integration with prompt caching on system prompt + Ghana admin reference data; tools: `geocode_ghana_location`, `lookup_population_density`, `query_historical_alerts`, `assess_emergency_severity`, `draft_cap_advisory`; user types free-form text in Manual Entry tab, agent populates CAP JSON for human review/edit before submission.
- [ ] **Phase 7: Globe Revamp + UI Polish + Pipeline Detail Audio/Translation Surfaces** — replace random-Bezier wireframe globe with `react-globe.gl` great-circle arcs anchored at named Ghana + neighboring cities (matches `Screenshot 2026-05-08 141301.png` aesthetic), add framer-motion tab/state transitions and alert-state animations, add translations + per-language audio players + MNO/SMS/public-feed dispatch status to the Pipeline tab detail view.
- [ ] **Phase 8: Public Display Endpoint** — `POST /public/feed/receive` accepts dispatched JSON from `dispatch_service.dispatch_to_mno` and broadcasts on a public Socket.IO namespace; `GET /public/feed/display` renders a TV-display HTML page (revive/replace `templates/tv_display.html`) showing the latest alert in full-screen with map zoom + audio playback + headline; `MNO_WEBHOOK_URL` defaults to this endpoint so the loop closes locally for testing; per-IP rate limit + optional signed viewer token query param for embedded screens.
- [ ] **Phase 9: Tests + Visual Regression** — pytest unit tests for services (mock external APIs); Flask test client for endpoint flows (login, manual entry, validator approval, public feed, GMeT webhook); Playwright E2E via the `webapp-testing` skill (login with real Africa's Talking sandbox SMS, manual entry with AI agent, validator approval, public feed broadcast); screenshot regression at key states (dark/light, alert expanded, map zoomed, globe loaded).
- [ ] **Phase 10: Full E2E Acceptance — PRD §6 + Overhaul Acceptance** — run the original PRD §6 7-criterion acceptance protocol end-to-end against the upgraded platform; additionally verify: docker build/run succeeds, no secrets in source tree, AI agent populates CAP from "heavy rain expected at Osu in Accra", globe matches reference screenshot, public display renders the latest alert, all Phase 1-9 acceptance criteria green.

## Phase Details

### Phase 1: Build/Infra Hygiene + Logic Bug Sweep + Critical Secrets to Env
**Goal**: A `gunicorn ghana_cap_app:app` deploy boots cleanly from Procfile or Dockerfile; a GMeT webhook POST auto-dispatches within 5 seconds (no validator gate); the manual entry form no longer crashes on missing lat/lon; validator approval uses an indexed find_one; SECRET_KEY and GMeT webhook API key are read from env vars while preserving current values to avoid breaking the active GMeT contract or invalidating sessions.
**Depends on**: Nothing (first phase — addresses INGEST-CONFLICTS.md INFO #3 plus the full logic-bug list from the overhaul brief)
**Requirements**: REQ-build-infra-hygiene, REQ-fix-workflow-stage-gate, REQ-fix-latlon-empty-string, REQ-fix-validator-scan, REQ-env-var-secrets, REQ-gmet-webhook-endpoint, REQ-gmet-webhook-auth, REQ-cap-payload-parsing, REQ-mno-webhook-dispatch, REQ-sms-dispatch
**Success Criteria** (what must be TRUE):
  1. A POST to `/api/v1/alerts/gmet/webhook` carrying a valid CAP v1.2 JSON body and a valid API-key header is parsed, validated, persisted, enriched, and dispatched to the MNO webhook **without any validator-approval step** — same request as ingress.
  2. Wall-clock latency from GMeT POST receipt to MNO webhook receipt is **≤ 5 seconds** under nominal local conditions (PRD §6 acceptance #5).
  3. Pre-registered test phone numbers receive a concise SMS on the same trigger (PRD §6 acceptance #6); SMS uses real Twilio when creds present, logs-only when absent (graceful-degradation invariant).
  4. The GMeT webhook API key and Flask `SECRET_KEY` are read from environment variables — no hardcoded literals remain in `ghana_cap_app.py`. Migration preserves the active GMeT contract (existing key value moved to env, not silently rotated) and existing session validity.
  5. `Procfile` and `Dockerfile` reference `ghana_cap_app:app` (not `app:app`); a fresh deploy from either artifact boots the current codebase.
  6. The manual entry form does not crash when lat/lon hidden inputs are empty strings — defaults are used or the form requires map click before submit.
  7. Validator approval (`/api/v1/alerts/validate/<identifier>`) uses a single MongoDB find_one (`db.find_alert_by_identifier`), not a full collection scan.
  8. `.env.example` documents all required and optional env vars; no live secrets in the example file.
**Plans**: TBD

### Phase 2: Security Hardening + Real-API 2FA via Africa's Talking
**Goal**: The web portal is hardened against common web attacks (CSRF, brute force, session forgery, secret leakage) and the email-+-6-digit "2FA" is replaced with real-API SMS 2FA via Africa's Talking that can be exercised against a sandbox account in tests.
**Depends on**: Phase 1
**Requirements**: REQ-real-2fa-africastalking, REQ-rate-limiting, REQ-csrf, REQ-secure-session, REQ-cors-lockdown, REQ-cryptographic-rng, REQ-tighten-allowed-ips, REQ-remove-dashboard-secret-leakage, REQ-secret-rotation
**Success Criteria** (what must be TRUE):
  1. Login uses `secrets.randbelow(900000) + 100000` for the 6-digit code (not `random.randint`).
  2. `/login` is rate-limited via Flask-Limiter (per-IP) with lockout after N failed verification attempts.
  3. Flask-WTF CSRF protection is active on all state-changing routes; JSON endpoints use a token mechanism that survives Socket.IO real-time updates.
  4. Session cookies are `Secure`, `HttpOnly`, `SameSite=Lax` (or `Strict` for the admin path).
  5. Socket.IO `cors_allowed_origins` is restricted to known origins (env-var driven), not `"*"`.
  6. Africa's Talking SMS 2FA is integrated; verification code is delivered via SMS to the user's phone number (stored in user record); when AT credentials are absent, falls back to logging the code (graceful-degradation invariant). Twilio remains as a fallback adapter.
  7. Dashboard Settings tab no longer prints the GMeT webhook key or Twilio SID. The `templates/ghana_cap_dashboard.html` lines 513 and 518 secret-leak references are removed.
  8. Three of four seed users no longer have `allowed_ips: ["*"]` — IP gate is either tightened to a documented allowlist or removed entirely in favor of proper auth.
  9. All previously-leaked credentials (MongoDB password, OpenAI key, Twilio Auth Token) are documented as rotated; new values live only in `.env` (gitignored) and `.env.example` shows placeholders.
**Plans**: TBD

### Phase 3: Enrichment Quality Upgrade
**Goal**: Translations and TTS run against real APIs (not silently mocked due to malformed env value), with native-quality voices for Twi/Ga/Ewe via Khaya and high-quality Hausa, while preserving the graceful-degradation pattern.
**Depends on**: Phase 1 (env-var pattern), Phase 2 (rotated secrets)
**Requirements**: REQ-translation-batching, REQ-tts-language-quality, REQ-fix-malformed-env-key, REQ-geo-resolution, REQ-translation, REQ-tts
**Success Criteria** (what must be TRUE):
  1. `OPENAI_API_KEY` is read as a bare key string (not the malformed `OpenAI(api_key="…")` expression). After this fix, real translations and real OpenAI TTS are used instead of mock fallbacks when the key is set.
  2. Translation makes a single OpenAI call returning a structured JSON object with all target languages (English, Twi, Hausa) — no longer N+1 sequential roundtrips.
  3. Twi (and Ga / Ewe when added in v2) are spoken in native voices via Ghana NLP Khaya TTS — no longer English-pronounced phonetics from OpenAI alloy.
  4. Hausa is spoken via Google Cloud TTS or Khaya (whichever produces native-quality output for the user's listening test).
  5. Without API credentials, the system still produces translation strings and audio file paths (mock fallbacks per existing graceful-degradation pattern) — the app must boot and the pipeline must complete end-to-end with zero external creds.
**Plans**: TBD

### Phase 4: Frontend Migration to React + Vite + TypeScript + Tailwind + framer-motion
**Goal**: The operator dashboard is a React SPA served by Flask (or via split origins), styled with Tailwind + a glassmorphic component library, animated with framer-motion. Light/dark theme is ported (not rebuilt). All existing tabs (Pipeline, Manual Entry, Settings) plus the PRD §4 Webhook Config and Test Dispatcher screens render under the new stack.
**Depends on**: Phase 3 (enrichment data is what the frontend renders)
**Requirements**: REQ-react-vite-frontend, REQ-flask-json-api-only, REQ-tailwind-glassmorphic-system, REQ-framer-motion-transitions, REQ-port-light-dark, REQ-dashboard-active-alerts-view, REQ-dashboard-webhook-config, REQ-dashboard-test-dispatcher, REQ-design-language-glassmorphism
**Success Criteria** (what must be TRUE):
  1. `frontend/` Vite project builds cleanly to `frontend/dist/`; Flask serves `dist/index.html` at `/` and `dist/assets/*` under `/assets/`.
  2. The Pipeline tab renders alerts in real time via Socket.IO `new_alert` / `alert_updated` events (no more `location.reload()` hack).
  3. Light/dark theme toggle works exactly like the current Jinja implementation (localStorage-persisted, body data-attribute driven), powered by a React-friendly equivalent (e.g. `next-themes` or a custom hook).
  4. All existing Flask routes serving HTML (`/`, `/login`) either still serve their Jinja templates (for login.html) OR are migrated to render the React shell (for `/` dashboard); state-changing routes remain JSON-only.
  5. Webhook Config screen lets operators view/generate/revoke GMeT API keys without editing files (PRD §4).
  6. Test Dispatcher button injects a mock GMeT JSON payload and streams it through Pipeline tab (PRD §4).
  7. Glassmorphic styles match or exceed the current Jinja implementation — semi-transparent backgrounds with backdrop-blur, subtle borders, layered drop shadows, dark-mode friendly.
**Plans**: TBD
**UI hint**: yes

### Phase 5: Map UX — Mapbox Globe, Region/District Selectors, NL Geocoding, flyTo, Rain Animation Overlay
**Goal**: The Manual Entry tab includes a Mapbox globe (MapLibre fallback) with region + district dropdowns wired to Ghana admin boundaries, plus a natural-language location input that triggers `flyTo` on the resolved coordinates. When the alert category is meteorological and the event keyword matches rain/storm/flood, a rain animation overlay activates over the affected area in real time during CAP creation.
**Depends on**: Phase 4 (React frontend hosts the map components)
**Requirements**: REQ-globe-mapbox, REQ-region-district-selectors, REQ-natural-language-location, REQ-map-flyto-zoom, REQ-rain-animation-overlay, REQ-ghana-admin-geojson-districts
**Success Criteria** (what must be TRUE):
  1. A region dropdown lists all 16 Ghana regions sourced from `static/ghana_regions.json`; selecting a region populates a districts dropdown via a Ghana admin-2 GeoJSON (added to `static/`).
  2. A natural-language location input accepts free-form text like "Osu in Accra" and resolves to lat/lon via a geocoder (Mapbox Geocoding API biased to Ghana, OR Nominatim fallback); on resolve, the map performs `flyTo` with smooth animation.
  3. When the user types "heavy rain expected at Osu in Accra" in the natural-language input or matching event field, the map flies to Osu and a rain animation overlay activates on the affected area in real time during CAP creation.
  4. The overlay supports rain (default), storm, and flood variants; activates only for category=Met events.
  5. The map renders correctly in both light and dark modes (using Mapbox style switching).
**Plans**: TBD

### Phase 6: AI Advisory Agent — Claude Sonnet 4.6 with Tool Use + Structured CAP JSON
**Goal**: A natural-language input on the Manual Entry tab invokes a Claude-based agent that geocodes the location, classifies the emergency type/severity/urgency/certainty, looks up affected population density and historical context, and drafts a CAP-conformant advisory (headline, description, instruction). Output populates the form for human review/edit before submission.
**Depends on**: Phase 4 (React UI hosts the agent interaction), Phase 5 (geocoder is one of the agent's tools)
**Requirements**: REQ-ai-advisory-agent, REQ-natural-language-cap-draft, REQ-tool-geocode, REQ-tool-population, REQ-tool-historical, REQ-tool-severity, REQ-tool-draft-advisory, REQ-prompt-caching
**Success Criteria** (what must be TRUE):
  1. A "Draft from natural language" button on the Manual Entry tab takes free-form input and calls a backend `/api/v1/agents/draft` endpoint that runs the Claude agent with tool use.
  2. The agent has access to five tools: `geocode_ghana_location`, `lookup_population_density`, `query_historical_alerts`, `assess_emergency_severity`, `draft_cap_advisory`. Each tool is implemented and tested.
  3. Agent output is a structured CAP JSON object (matching the Manual Entry form schema): identifier, category, event, urgency, severity, certainty, headline, description, instruction, latitude, longitude, affected_regions.
  4. The user can edit any field before submitting; the agent's draft is a starting point, never an auto-submission.
  5. System prompt + Ghana admin reference data are cached via Anthropic's prompt caching for cost efficiency.
  6. Without `ANTHROPIC_API_KEY`, the endpoint returns a clearly-marked mock advisory (graceful-degradation invariant).
  7. End-to-end test: typing "heavy rain expected at Osu in Accra" produces a populated CAP form with category=Met, event mentioning rain, severity=Severe or Moderate, lat/lon close to Osu (5.5567, -0.1820), and a sensible headline + advisory text.
**Plans**: TBD

### Phase 7: Globe Revamp + UI Polish + Pipeline Detail Audio/Translation Surfaces
**Goal**: The dashboard background globe matches the `Screenshot 2026-05-08 141301.png` aesthetic — a dark navy globe with cyan/teal great-circle arcs anchored at named Ghana + neighboring cities. Tab and state transitions use framer-motion. The Pipeline tab detail view surfaces translations, per-language audio players, and full dispatch status (MNO, SMS, public-feed).
**Depends on**: Phase 4 (React shell), Phase 8 (public-feed status surfaces from there) — or run in parallel and stub public-feed status if Phase 8 lands later
**Requirements**: REQ-globe-anchored-arcs, REQ-globe-aesthetic-match, REQ-pipeline-detail-translations, REQ-pipeline-detail-audio-players, REQ-pipeline-detail-dispatch-status, REQ-framer-motion-polish
**Success Criteria** (what must be TRUE):
  1. The dashboard background uses `react-globe.gl` (Three.js wrapper) rendering a dark globe with great-circle arcs between named city anchors (Accra, Kumasi, Tamale, Sekondi-Takoradi, plus Lomé, Abidjan, Ouagadougou, Lagos, Lagos as neighbors). Arcs animate (animated dash or pulse) similar to the reference screenshot.
  2. Visual comparison against `Screenshot 2026-05-08 141301.png` confirms the dark + cyan/teal arc + city-anchored aesthetic.
  3. Tab transitions (Pipeline ↔ Manual Entry ↔ Settings) and alert-card expand/collapse use framer-motion with smooth, fluid timing.
  4. Pipeline tab alert detail shows: English/Twi/Hausa translation tabs (or stacked sections), each with a `<audio>` player loaded from `audio_links[lang]`, each with a status badge indicating audio file existence (HEAD request to confirm).
  5. Dispatch status panel in the alert detail shows: MNO HTTP status code or "Not dispatched", SMS provider IDs or "Failed/Mocked", public-feed broadcast confirmation or "Pending".
**Plans**: TBD
**UI hint**: yes

### Phase 8: Public Display Endpoint
**Goal**: A public URL `/public/feed/display` shows the latest dispatched alert in full-screen TV-display style (map zoom + audio + headline + animated). Dispatched alerts are POSTed to `/public/feed/receive` and broadcast on a public Socket.IO namespace. `MNO_WEBHOOK_URL` defaults to this local endpoint for end-to-end testing.
**Depends on**: Phase 1 (dispatch already wired), Phase 7 (audio surfaces, TV display revives `tv_display.html` foundation)
**Requirements**: REQ-public-mno-receiver, REQ-public-display-page, REQ-public-socketio-namespace, REQ-mno-webhook-default-loops-back, REQ-public-rate-limit
**Success Criteria** (what must be TRUE):
  1. `POST /public/feed/receive` accepts the dispatched JSON payload from `dispatch_service.dispatch_to_mno`, stores it in memory (or MongoDB `public_feed` collection), and emits to the public Socket.IO namespace `/live_feed`.
  2. `GET /public/feed/display` renders a full-screen TV-display HTML page that subscribes to `/live_feed` and renders the latest alert: headline, severity badge, affected regions, map zoomed to the affected area, audio player auto-playing the language matching the regional default.
  3. `MNO_WEBHOOK_URL` env var defaults to `http://localhost:5000/public/feed/receive` when unset, so the dispatch loop closes locally for testing without requiring an external MNO endpoint.
  4. The display page is publicly accessible (no login), but per-IP rate limited to prevent abuse.
  5. An optional signed viewer token query param (`?viewer=<jwt>`) allows long-lived embedding in TV displays without rate-limit interference.
  6. The existing `data_receiver.py` script (which subscribes to `/live_feed`) successfully consumes events.
**Plans**: TBD

### Phase 9: Tests + Visual Regression
**Goal**: pytest covers services and endpoint flows; Playwright (via the `webapp-testing` skill) covers the user-facing E2E flows; screenshot regression catches visual drift at key states.
**Depends on**: Phases 1-8 (cannot test what isn't built)
**Requirements**: REQ-tests-unit-integration, REQ-tests-playwright-e2e, REQ-tests-visual-regression
**Success Criteria** (what must be TRUE):
  1. `pytest tests/services/` passes with mocked external APIs covering geo_service, enrichment_service, dispatch_service, email_service, external_analytics_service, and the AI agent tools.
  2. `pytest tests/integration/` passes with Flask test client covering: login (mock AT SMS), manual_alert, gmet_webhook (auto-dispatch path), validate_alert (approve + reject), public feed (POST + GET), and `/api/v1/agents/draft`.
  3. Playwright E2E (run via `webapp-testing` skill) covers: login (real AT sandbox SMS), manual entry with AI agent draft, validator approval flow, public feed broadcast.
  4. Screenshot regression captures key states: dark dashboard, light dashboard, alert detail expanded with audio players visible, map flyTo zoomed to Osu with rain overlay, globe loaded with arcs visible, public display rendering an alert.
  5. CI runs all tests on every commit; the test command is documented in README.md.
**Plans**: TBD

### Phase 10: Full E2E Acceptance — PRD §6 + Overhaul Acceptance
**Goal**: The full Milestone 1 acceptance protocol passes — the original PRD §6 7-criterion test plus the overhaul acceptance gates from Phases 1-9.
**Depends on**: Phase 9
**Requirements**: REQ-event-logging (PRD acceptance #7) plus the entire prior phase set's success criteria reconfirmed end-to-end
**Success Criteria** (what must be TRUE):
  1. PRD §6 acceptance protocol passes all 7 criteria green: (1) GMeT webhook receives valid POST, (2) geo-resolution to district/region accurate, (3) translation to ≥1 local language successful with native-quality voices, (4) TTS audio link playable, (5) MNO endpoint receives enriched JSON within 5s, (6) test SMS numbers receive alert text, (7) all events logged in MongoDB.
  2. `docker build . && docker run` boots the platform; the GMeT webhook accepts a valid CAP payload within 30 seconds of container start.
  3. No live secrets in source tree (verified by `git grep -E '(sk-|AC[0-9a-f]{32}|mongodb\\+srv://[^@]+@)'`).
  4. The user can submit "heavy rain expected at Osu in Accra" in Manual Entry, the AI agent populates a CAP draft, the map flies to Osu with rain overlay, and the operator submits + dispatches.
  5. Visiting `/public/feed/display` renders the latest dispatched alert in full-screen with audio playback.
  6. `pytest && playwright test` passes locally and in CI.
  7. Light/dark mode toggle works on every screen including the public display.
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10. Decimal insertions (e.g., 1.1, 2.1) execute between their surrounding integers if added later via `/gsd-insert-phase`.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Build/Infra Hygiene + Logic Bug Sweep + Critical Secrets to Env | 0/TBD | In progress (direct execution, no plan yet) | - |
| 2. Security Hardening + Real-API 2FA via Africa's Talking | 0/TBD | Not started | - |
| 3. Enrichment Quality Upgrade | 0/TBD | Not started | - |
| 4. Frontend Migration to React + Vite + TypeScript + Tailwind + framer-motion | 5/5 (all plans shipped; Playwright E2E 20/20 PASS via tests/e2e_smoke.py) | Complete | 2026-05-09 |
| 5. Map UX — Mapbox Globe, Region/District Selectors, NL Geocoding, flyTo, Rain Animation Overlay | 0/TBD | Not started | - |
| 6. AI Advisory Agent — Claude Sonnet 4.6 with Tool Use + Structured CAP JSON | 0/TBD | Not started | - |
| 7. Globe Revamp + UI Polish + Pipeline Detail Audio/Translation Surfaces | 0/TBD | Not started | - |
| 8. Public Display Endpoint | 0/TBD | Not started | - |
| 9. Tests + Visual Regression | 0/TBD | Not started | - |
| 10. Full E2E Acceptance — PRD §6 + Overhaul Acceptance | 0/TBD | Not started | - |
