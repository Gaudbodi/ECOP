# Changelog

All notable changes to the Ghana National CAP Platform are tracked here. Format
loosely follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased] — Milestone 1 overhaul (in progress, started 2026-05-09)

### Phase 1 — Build/Infra Hygiene + Logic Bug Sweep + Critical Secrets to Env

#### Fixed

- **`Procfile`** now points at `ghana_cap_app:app` (was the deleted `app:app`).
- **`Dockerfile` CMD** now points at `ghana_cap_app:app`.
- **`gmet_webhook` auto-dispatches** at `workflow_stage=3` so PRD §6 acceptance
  #5 (≤5s GMeT → MNO dispatch) holds. Previously defaulted to stage 1
  (validator gate). Resolves `INGEST-CONFLICTS.md` INFO #3.
- **`process_alert_logic` lat/lon empty-string crash**: the manual entry form
  ships empty hidden inputs until the map is clicked, and `float("")` raised
  `ValueError`. Added `_coord_or_default` helper.
- **`validate_alert` full collection scan**: replaced
  `next(a for a in get_all_alerts())` with `db.find_alert_by_identifier`
  (single MongoDB `find_one`).
- **`SECRET_KEY`** read from `FLASK_SECRET_KEY` env var (literal fallback for
  Phase 1 boot continuity; warning logged when fallback is in use).
- **GMeT webhook API key** read from `GMET_WEBHOOK_API_KEY` env var (literal
  fallback as above).

#### Added

- **`db.find_alert_by_identifier(identifier)`** helper (`find_one`-based).
- **`.env.example`** documenting all required and optional env vars across
  phases 1-8.

#### Changed

- **`requirements.txt`** added: `flask-limiter`, `flask-wtf`, `python-dotenv`,
  `anthropic`, `africastalking`, `psycopg2-binary`. Run `pip install -r
  requirements.txt` before Phase 2.
- **`.dockerignore`** expanded to exclude `.env`, `*.zip`, `*.pdf`, screenshots,
  `.venv/`, `.git/`, `.planning/`, `static/audio/`, frontend `node_modules/`
  and `dist/`, deprecated `app[DEPRECATED].py`, the requirements PDF.

### Phase 2 — Security Hardening + Real-API 2FA via Africa's Talking

#### Added

- **`services/sms_2fa_service.py`**: Africa's Talking primary + Twilio fallback
  + log-only graceful-degradation. Singleton matching the existing services
  pattern.
- **`db.is_email_locked()`**, lockout tracking on `verification_codes` docs:
  5 failed verification attempts → 30-minute lockout. Successful verify clears
  the counter.
- **`db._operator_allowed_ips()`** reads `ALLOWED_OPERATOR_IPS` env var
  (comma-separated, default `127.0.0.1,::1`); set to `*` for legacy
  any-IP behaviour during rollout.
- **Phone numbers** added to seed users (`phone_number` field) for SMS 2FA.
  Defaults are `+233000000001..4` placeholders; override via
  `ADMIN_PHONE_NUMBER`, `GENERATOR_PHONE_NUMBER`, `VALIDATOR_PHONE_NUMBER`,
  `NADMO_PHONE_NUMBER` env vars.

#### Changed

- **Verification code RNG** now uses `secrets.randbelow(900000) + 100000`
  (was `random.randint`, not crypto-secure).
- **`allowed_ips`** for non-Admin seed users now reads from
  `ALLOWED_OPERATOR_IPS` env (default localhost) instead of `["*"]`. Admin
  retains tighter `["127.0.0.1", "::1", "10.0.0.1"]` defense-in-depth.
- **Login flow** sends the verification code via SMS (Africa's Talking →
  Twilio fallback → log-only) when the user has a `phone_number`; falls back
  to email when no phone is on file.
- **`templates/ghana_cap_dashboard.html`** Settings tab: removed plaintext
  display of the GMeT webhook API key and the Twilio Account SID. Replaced
  with "(configured server-side)" placeholders.

### Phase 3 — Enrichment Quality Upgrade

#### Added

- **`KhayaTTSClient`** in `services/enrichment_service.py` — REST client for
  Ghana NLP Khaya TTS. Per-language dispatch in `text_to_speech`:
  - **English** → OpenAI tts-1 (`alloy`)
  - **Twi / Ga / Ewe** → Khaya, falling back to OpenAI tts-1 (`onyx`)
  - **Hausa** → Khaya, falling back to OpenAI tts-1 (`onyx`)
  - **Other** → OpenAI tts-1 (`alloy`)
- **`load_dotenv()`** at the top of `ghana_cap_app.py` so `.env` is loaded
  reliably regardless of how the app is launched.
- **Malformed `OPENAI_API_KEY` detection** — the literal Python expression
  `OpenAI(api_key="sk-…")` (which the user's `.env` carried before Phase 3)
  is detected and treated as missing, with a single loud warning. Prevents
  confusing "401 Unauthorized" errors and surfaces the fix clearly.
- **`KHAYA_API_KEY`, `KHAYA_API_BASE`** documented in `.env.example`.

#### Changed

- **`translate_text` is now a single batched OpenAI call** with
  `response_format={"type": "json_object"}` returning a structured dict of
  all language variants. Was N sequential roundtrips (one per language).

### Phase 4 — Frontend Migration to React + Vite + TypeScript + Tailwind + Motion

#### Added

- **`frontend/`** — Vite 6 + React 19 + TypeScript 5.9 + Tailwind 4.3 + Motion
  12.38 + socket.io-client 4.8 SPA project. Dev server runs on `:5173` and
  proxies `/api`, `/socket.io` (with `ws:true`), and `/static` to Flask
  `:5000`. Production `npm run build` writes hashed assets to
  `frontend/dist/` which Flask serves at `/` + `/assets/`.
- **`GET /api/v1/me`** — returns current session user JSON for the React
  navbar / role-gating. Login required; honors the existing session cookie.
- **`GET /api/v1/alerts`** — JSON alert list for the Pipeline tab.
  Stringifies Mongo `_id`. Graceful-degradation: returns 200 +
  `{degraded: true, alerts: []}` when Mongo is unreachable instead of 500.
  Login required.
- **`POST /api/v1/dispatcher/test`** — Admin-only Test Dispatcher endpoint.
  Injects a fixed synthetic CAP payload through `process_alert_logic` at
  `workflow_stage=3` so it traces the full ingest → enrich → dispatch path
  and surfaces in Pipeline via `new_alert`. Server-side proxy keeps the
  GMeT API key out of the browser.
- **Tailwind 4 CSS-first theme** — `frontend/src/index.css` ports the
  `--bg-color`, `--glass-bg`, `--glass-border`, `--accent-color`, etc.
  tokens from the legacy dashboard verbatim into a `@theme` block, with a
  `@custom-variant dark (&:where([data-theme=dark], [data-theme=dark] *))`
  selector matching the existing `data-theme` attribute strategy.
- **`useTheme`, `useApi`, `useAlerts`, `useValidation`** — React hooks
  porting the legacy theme + state behavior. `useAlerts` subscribes to the
  Socket.IO singleton's `new_alert` and `alert_updated` events with
  immutable state updates — no `location.reload()`.
- **`<RejectDialog>`** — `<dialog>`-based modal replacing the legacy
  `prompt('Reason for rejection:')`.
- **`<MapPanel>`** — thin Leaflet wrapper kept (per phase plan: Phase 5
  swaps to Mapbox). Theme-reactive tile (CARTO `dark_all` / `light_all`)
  + `invalidateSize` on tab visibility, replacing the legacy
  `setTimeout(() => map.invalidateSize(), 100)`.
- **`<GlobePlaceholder>`** — static gradient backdrop standing in for the
  Phase 7 `react-globe.gl` revamp. Documented Phase 7 SWAP POINT inline.
- **Backend tests** — added 13 new pytest cases covering the three new
  endpoints and the SPA-serve route in `tests/test_endpoints.py`.

#### Changed

- **Flask `dashboard()` route** — now serves `frontend/dist/index.html`
  via `send_from_directory(FRONTEND_DIST, 'index.html')`. The legacy
  Jinja `render_template('ghana_cap_dashboard.html', alerts=..., user=...)`
  is gone; the SPA fetches alerts + user via `GET /api/v1/alerts` and
  `GET /api/v1/me`.
- **`@csrf.exempt` posture preserved** — JSON endpoints stay CSRF-exempt
  under the existing SameSite=Lax + HttpOnly + Secure-in-prod cookie
  defense. Token-in-header CSRF deferred to a future hardening pass.
- **`ALLOWED_ORIGINS` defaults** — already include `http://localhost:5173`
  (Vite dev) from Phase 2; no change needed in Phase 4.
- **`.env.example`** — appended a Phase 4 frontend section documenting
  optional `VITE_*` env vars (no secrets).
- **`.gitignore`** — added `frontend/node_modules/`, `frontend/dist/`,
  `frontend/.vite/` to repo root ignores.
- **Webhook Config (Settings tab)** — read-only per the Phase 4
  pre-resolved assumptions A5/A7. Shows webhook URL via plain JSX
  (replacing the legacy `<script>document.write(...)</script>`), masked
  key, rotation instructions, and a clear note that generate/revoke
  controls are deferred to a follow-up phase.

#### Fixed

- **`location.reload()` × 3** — the legacy dashboard reloaded the entire
  page on `new_alert`, after manual submit, and after validator approve.
  Replaced with reactive state updates via `useAlerts` + Socket.IO. CAP
  alerts now stream to operator dashboards in true real-time without
  killing the WebSocket connection.
- **`<script>document.write(...)</script>`** — the legacy webhook URL
  display used `document.write` after page load (a no-op on a parsed
  document; "worked" only because it ran inline). Replaced with
  `{`${origin}/api/v1/alerts/gmet/webhook`}` JSX.
- **`prompt('Reason for rejection:')`** — replaced with the
  `<RejectDialog>` modal (proper accessibility, validation, cancel flow).
- **`max-height: 500px` expand kludge** — the legacy alert detail
  expand-collapse used a CSS `max-height: 0 ↔ 500px` transition that
  clipped long descriptions. Replaced with framer-motion
  `height: 0 ↔ 'auto'` which measures correctly.
- **Mongo `ObjectId` JSON serialization** — `GET /api/v1/alerts`
  stringifies `_id` (mirrors the existing `validate_alert` fix at
  `ghana_cap_app.py:278-280`).

#### Removed

- **`templates/ghana_cap_dashboard.html`** — deleted. Git history
  preserves the source for reference. The React SPA in `frontend/src/`
  is the canonical operator dashboard going forward.
- **Three.js wireframe globe init code** (was inline at
  `ghana_cap_dashboard.html:546-626`) — not ported. Phase 7 will
  introduce `react-globe.gl` per ROADMAP §7. Until then, a static
  gradient backdrop renders behind the shell.

#### Deferred / Follow-up

- **Webhook Config generate/revoke** (REQ-dashboard-webhook-config full
  scope) — requires a Mongo `webhook_keys` collection + multi-key auth
  check at `gmet_webhook` + UI rotation flow. Plan 04's read-only Webhook
  Config surfaces the deferral inline.
- **Header-CSRF on JSON endpoints** — current SameSite=Lax + HttpOnly +
  Secure-in-prod is the v1 defense. A follow-up phase can add
  `X-CSRFToken` header validation if the threat model demands it.
- **Globe revamp** — Phase 7 owns the `react-globe.gl` swap. The
  `<GlobePlaceholder>` carries a Phase 7 SWAP POINT comment so the
  swap is one-file-local.
- **Vitest + Playwright** — Phase 9 owns the React component test runner
  and E2E coverage. Phase 4 ships with backend pytest only.

### Phase 6 — AI Advisory Agent (Claude Sonnet 4.6 + tool use)

#### Added

- **`services/advisory_agent_service.py`** — Anthropic SDK with tool-use loop
  + structured CAP JSON output. Five tools as specced:
  - `geocode_ghana_location(text)` — static table (~50 places) → Nominatim
    fallback. Type-priority resolution so "Osu in Accra" returns Osu
    (neighborhood), not Accra (city).
  - `lookup_population_density(region, district?)` — Ghana 2021 census
    figures from the static reference table.
  - `query_historical_alerts(region, event_type?)` — MongoDB scan via
    `db.get_all_alerts`, filtered by region + event-keyword substring.
  - `assess_emergency_severity(event_type, area_population, time_of_year)`
    — rule table with population/season bumps.
  - `draft_cap_advisory(event_type, severity, area, language, description)`
    — templated headline + description + instruction text per event class.
- **`services/_ghana_reference.py`** — static reference data (16 regions,
  ~50 places, season calendar, density helper).
- **`POST /api/v1/agents/draft`** endpoint (login required, CSRF-exempt
  matching the JSON-API pattern, rate-limited 30/hour). Body
  `{"text": "..."}`, returns CAP-shaped JSON for the Manual Entry form.
- **Prompt caching** — system prompt + Ghana admin reference embedded as a
  cacheable text block (`cache_control: ephemeral`). Subsequent calls
  within the cache TTL re-use the cached prefix.
- **Graceful-degradation mock** — without `ANTHROPIC_API_KEY`, the service
  returns a clearly-marked mock CAP draft (uses the static geocoder so the
  mock still resolves Osu / Tamale / etc.). UI flow remains testable.

#### Smoke test

`POST /api/v1/agents/draft` with `{"text": "heavy rain expected at Osu in
Accra"}` returns:
```
headline: [MOCK] Rain alert for Osu
event: Rain   severity: Moderate
lat/lng: 5.5567, -0.182   region: Greater Accra
agent.mock: true (because ANTHROPIC_API_KEY isn't set)
```

Empty input → 400. Unauthenticated → 302 to /login.

### Phase 8 — Public Display Endpoint

#### Added

- **`POST /public/feed/receive`** accepts the dispatched MNO payload from
  `dispatch_service.dispatch_to_mno`. Caches the latest alert in module
  state and broadcasts it on the `/live_feed` Socket.IO namespace so any
  connected TV display updates in real time. CSRF-exempt (public, no
  session). Per-IP rate limited at 60/minute.
- **`GET /public/feed/display`** renders `templates/public_feed.html` —
  full-screen dark TV-style page. Shows headline / severity / urgency +
  certainty / affected regions / event / sender / sent timestamp, plus
  per-language audio tabs (English default, Twi/Hausa selectable) with
  auto-play, plus a Leaflet map zoomed to the affected coordinates.
  Subscribes to `/live_feed` and re-renders on every incoming alert.
  Public, no login. Per-IP rate limited at 120/minute.
- **`/live_feed` Socket.IO namespace** is now actually emitted to (was
  referenced by `data_receiver.py` but never produced — the dead-code
  finding from the ingest is now resolved). On connect, new subscribers
  receive the cached latest alert as bootstrap.

#### Changed

- **`MNO_WEBHOOK_URL`** default in `services/dispatch_service.py` is now
  `http://localhost:5000/public/feed/receive` (was port 5001 mock). The
  dispatch loop closes locally for testing without a separate MNO process.
  Production deploys override via `MNO_WEBHOOK_URL` env var.

### Phase 9 — Tests + Visual Regression (backend portion)

#### Added

- **`tests/conftest.py`** with shared fixtures: app fixture (TESTING mode,
  CSRF disabled, Limiter disabled), anonymous client, authenticated admin
  client, sample dispatch payload.
- **`tests/test_endpoints.py`** — 12 tests covering login render, logout,
  GMeT webhook auth (missing/wrong/correct key), manual alert auth + empty
  lat/lon tolerance (Phase 1 fix), agents/draft auth + mock CAP shape +
  empty-input rejection, public feed empty state + receive + display +
  malformed body.
- **`tests/test_services.py`** — 14 tests covering geo_service, lookup_place
  type priority, enrichment translation/TTS mock fallbacks, advisory agent
  five tools standalone, advisory agent mock response with static geocoder,
  SMS 2FA log-only fallback.
- **`requirements.txt`** + venv install of `pytest`, `pytest-flask`.

#### Result

`pytest tests/` → **26 passed in ~36s**.

The Playwright E2E portion (login with real Africa's Talking sandbox SMS,
manual entry with the AI agent, validator approval, public feed broadcast,
visual regression) lands after Phase 4 (frontend migration) since several
flows exercise React components.

#### Operational note

A pre-existing `langsmith` install in the venv had a broken `zstandard`
dependency that prevented pytest from booting. Force-reinstalling
`zstandard` resolved it; documented here in case it reappears.

### Required user actions

These cannot be done from inside the codebase and require the user to act
externally before the affected Phase 2 features are real (rather than
graceful-degraded into log-only mode):

1. **Rotate the leaked credentials** that previously sat in `.env` (and in
   `db.py` line 9 / `PRD.txt` line 85 as fallback defaults):
   - **MongoDB Atlas password** for `cluster0.pcd3g.mongodb.net` — rotate in
     Atlas console; update `MONGO_URI` in `.env`. The platform's hardcoded
     fallback in `db.py` will be removed in Phase 2 follow-up.
   - **OpenAI API key** — rotate at platform.openai.com; set `OPENAI_API_KEY`
     in `.env` as a **bare key string** (the current value
     `OpenAI(api_key="sk-…")` is malformed and is being silently mocked;
     Phase 3 strictly fixes the format).
   - **Twilio Auth Token** — rotate at console.twilio.com; set
     `TWILIO_AUTH_TOKEN` in `.env`. Twilio Account SID currently hardcoded
     fallback in `dispatch_service.py` — Phase 2 follow-up will remove it.
2. **Generate a strong `FLASK_SECRET_KEY`** and set it in `.env`:
   ```
   python -c "import secrets; print(secrets.token_urlsafe(64))"
   ```
3. **Generate a fresh `GMET_WEBHOOK_API_KEY`** and coordinate the rotation
   with GMeT. Set the new value in `.env`. The Phase 1 fallback to
   `gh_cap_poc_key_2026` will be removed once GMeT confirms the new key.
4. **Set `AFRICASTALKING_USERNAME`, `AFRICASTALKING_API_KEY`,
   `AFRICASTALKING_FROM`** in `.env` (sandbox is fine for tests). Without
   these, SMS 2FA falls back to log-only — codes appear in the server log.
5. **Set per-user `ADMIN_PHONE_NUMBER` etc.** if you want SMS 2FA against
   real numbers in dev. Otherwise the placeholder `+2330000000…` numbers
   route to log-only.
6. **Fix `OPENAI_API_KEY` in `.env`** — the current value is the literal
   Python expression `OpenAI(api_key="sk-…")`, which Phase 3 detects and
   treats as missing. Edit `.env` so the line reads:
   ```
   OPENAI_API_KEY=sk-…   # bare key, no parens, no Python wrapping
   ```
   Until this is fixed, translations and TTS run in mock mode.
7. **Get a `KHAYA_API_KEY`** from Ghana NLP (https://ghananlp.org) for
   native-quality Twi / Ga / Ewe / Hausa TTS. Without it, African-language
   TTS falls back to OpenAI's English voice (functional but not native).
   *(Superseded — see Provider Migration below; Khaya was removed.)*

---

### Provider Migration — May 2026

Cross-cutting provider swap driven by upstream availability + cost
considerations. Three substitutions, all preserving the
graceful-degradation invariant.

#### Changed

- **Advisory agent: Anthropic Claude Sonnet 4.6 → Google Gemma 4** via
  the Gemini API (`google-genai` SDK). Default model is
  `gemma-4-26b-a4b-it`; alternate `gemma-4-31b-it`. Function-calling tool
  loop preserved verbatim — same five tools (geocode, population density,
  historical alerts, severity assessment, advisory drafting). The five
  tool implementations are unchanged; only the SDK surface and the
  multi-turn loop pattern moved from `client.messages.create` to
  `client.models.generate_content` with `types.Tool(function_declarations=...)`
  and `types.Part.from_function_response(...)`.
- **Email service: SMTP → Resend API** for OTP delivery. The
  `send_verification_email(receiver, code)` contract is unchanged. HTML
  and plaintext bodies are rendered inline; the synchronous
  `resend.Emails.send` is the only call. SMTP ports / app-password auth
  are gone. Default `RESEND_FROM` uses Resend's `onboarding@resend.dev`
  sandbox sender; production deployments should swap in a verified
  domain.
- **Enrichment service: removed Khaya (Ghana NLP) TTS** — `ghananlp.org`
  withdrew its public API. OpenAI `tts-1` is now the sole provider for
  every language. Per-language voice mapping retained
  (`English`→`alloy`; `Twi`/`Hausa`/`Ga`/`Ewe`→`onyx`) so the audio is
  still distinguishable, even if not natively pronounced. Native-voice
  follow-up depends on a future provider landing.

#### Removed

- `anthropic` Python package from `requirements.txt`.
- `KhayaTTSClient` class + `_KHAYA_LANG_CODE` map from
  `services/enrichment_service.py`.
- SMTP-based email plumbing from `services/email_service.py` (smtplib,
  MIMEText, MIMEMultipart, all `SMTP_*` env vars).
- Env vars: `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`, `KHAYA_API_KEY`,
  `KHAYA_API_BASE`, `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USERNAME`,
  `SMTP_PASSWORD`. All eight are gone from `.env.example`.

#### Added

- `google-genai>=0.3.0` and `resend>=2.0.0` in `requirements.txt`.
- Env vars: `GEMINI_API_KEY`, `GEMINI_MODEL`, `RESEND_API_KEY`,
  `RESEND_FROM` in `.env.example`.

#### Required user actions

1. **Run `pip install -r requirements.txt`** to pick up `google-genai`
   and `resend`. The old `anthropic` package can be uninstalled
   (`pip uninstall anthropic`).
2. **Set `GEMINI_API_KEY`** in `.env`. Get one from
   <https://aistudio.google.com>. Without it, the advisory agent
   continues to return mock CAP drafts via the static geocoder — the
   degradation path is unchanged.
3. **Set `RESEND_API_KEY`** in `.env`. Get one from
   <https://resend.com>. Without it, the OTP code is logged to stdout
   the same way the legacy SMTP fallback did.
4. **(Optional) Set `RESEND_FROM`** to a verified sender on your own
   domain for production. The default `onboarding@resend.dev` sandbox
   only delivers to the account owner's inbox.
5. **Remove `ANTHROPIC_*`, `KHAYA_*`, `SMTP_*`** lines from your local
   `.env` if they exist — they're no longer read by the app.

---

*This file was created 2026-05-09 as part of the Phase 2 secret-rotation
documentation requirement (REQ-secret-rotation in REQUIREMENTS.md).*
