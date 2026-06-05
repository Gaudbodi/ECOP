---
phase: 04-frontend-migration-to-react-vite-typescript-tailwind-framer-
plan: 01
subsystem: ui
tags: [react, vite, typescript, tailwindcss-v4, motion, leaflet, flask, spa, glassmorphism]

requires:
  - phase: 02-security-real-2fa-hardening
    provides: SameSite=Lax cookies, ALLOWED_ORIGINS allowlist (already includes localhost:5173), CSRFProtect with @csrf.exempt JSON-endpoint pattern
  - phase: 06-ai-advisory-agent
    provides: /api/v1/agents/draft endpoint shape (consumed by future Manual Entry tab)
  - phase: 08-public-display-endpoint
    provides: /live_feed Socket.IO namespace, public_feed_receive endpoint
provides:
  - Vite + React 19 + TypeScript 5.8 (SWC) project under frontend/ that builds clean
  - Tailwind v4 CSS-first theme (@theme + @custom-variant dark + @utility glass-card) ported verbatim from ghana_cap_dashboard.html:13-31
  - No-flash theme bootstrap (data-theme on <html> + <body> before React mount)
  - Flask serves frontend/dist/index.html at GET / via send_from_directory(FRONTEND_DIST, 'index.html')
  - Flask serves hashed Vite assets at GET /assets/<file>
  - GET /api/v1/me — returns session['user'] for SPA navbar + role gating
  - GET /api/v1/alerts — JSON envelope {alerts, degraded} with _id stringified + graceful-degradation fallback
  - POST /api/v1/dispatcher/test — Admin-only Test Dispatcher with server-side mock payload (GMeT key never reaches browser)
  - 11 new pytest tests; 37 total pass (26 prior + 11 new)
  - frontend/dist baseline: 4 files, 208 KB total (gzip JS 61 KB, gzip CSS 2.3 KB)
affects: [04-02, 04-03, 04-04, 04-05, 05, 07]

tech-stack:
  added:
    - react@19.1.1 + react-dom@19.1.1
    - vite@6.3.5 + @vitejs/plugin-react-swc@3.9.0
    - typescript@5.8.3
    - tailwindcss@4.3.0 + @tailwindcss/vite@4.3.0
    - motion@12.38.0 (canonical post-rebrand of framer-motion)
    - socket.io-client@4.8.3
    - leaflet@1.9.4 + leaflet-draw@1.0.4 (raw Leaflet, NOT react-leaflet)
    - lucide-react@1.14.0
    - clsx@2.1.1 + tailwind-merge@3.5.0 + class-variance-authority@0.7.1
    - @types/leaflet@1.9.21 + @types/leaflet-draw@1.0.13 + @types/react@19.1.16
  patterns:
    - "Vite dev proxy → Flask :5000 (/api, /socket.io with ws:true, /static)"
    - "Tailwind v4 CSS-first config (no tailwind.config.js, no postcss.config.js)"
    - "SPA-serve via send_from_directory + FRONTEND_DIST constant resolved relative to ghana_cap_app.py"
    - "JSON envelope {alerts, degraded} for graceful-degradation on Mongo failure"
    - "Server-side proxy for Test Dispatcher — API key never leaves backend"

key-files:
  created:
    - frontend/package.json
    - frontend/package-lock.json
    - frontend/vite.config.ts
    - frontend/tsconfig.json
    - frontend/tsconfig.app.json
    - frontend/tsconfig.node.json
    - frontend/index.html
    - frontend/src/main.tsx
    - frontend/src/App.tsx
    - frontend/src/index.css
    - frontend/src/vite-env.d.ts
    - frontend/.gitignore
    - frontend/eslint.config.js
    - frontend/README.md
  modified:
    - .gitignore (added frontend/node_modules/, frontend/dist/, frontend/.vite/)
    - .env.example (added Phase 4 frontend section)
    - ghana_cap_app.py (FRONTEND_DIST constant; rewrote dashboard(); added /assets, /api/v1/me, /api/v1/alerts, /api/v1/dispatcher/test, _TEST_DISPATCHER_MOCK_PAYLOAD)
    - tests/test_endpoints.py (11 new Phase 4 tests appended)

key-decisions:
  - "Pinned create-vite@6 (not latest@9) because 9.0.6 silently ignores --template react-swc-ts and produces a vanilla TS scaffold. RESEARCH.md A3 already flagged 6.x vs 8.x ambiguity; v9 is unusable for this template."
  - "Vite resolved to 6.3.5, TypeScript to 5.8.3, React to 19.1.x — registry-resolved at scaffold time. Plan explicitly permits this drift from RESEARCH.md's 6.0.3 / 5.9.3 / 19.2.6 baselines."
  - "Cleaned up scaffold cruft: removed src/App.css and src/assets/react.svg since the placeholder App.tsx no longer references them. Keeps the file list tight."
  - "Kept frontend/eslint.config.js and frontend/README.md from the scaffold — out of plan files_modified list but part of an idiomatic Vite project; harmless and removing them would create churn."
  - "tsconfig has verbatimModuleSyntax: true so the App import in main.tsx must be value (default) not type — confirmed working."

patterns-established:
  - "Pattern: Tailwind v4 CSS-first config — all theme tokens live in src/index.css under @theme; no JS config file. @custom-variant precedes @theme so the dark variant is registered for utilities."
  - "Pattern: No-flash theme bootstrap — inline <script> in index.html sets data-theme on <html> and <body> from localStorage before React mounts. Prevents dark→light flash on cold load."
  - "Pattern: SPA-serve in Flask — FRONTEND_DIST constant resolved relative to ghana_cap_app.py (works under both `python ghana_cap_app.py` and gunicorn). dashboard() route stays @login_required so unauthed users still redirect to /login."
  - "Pattern: Graceful-degradation JSON envelope — list_alerts returns {alerts, degraded:bool} so the SPA can render an empty state on Mongo failure instead of a 500."
  - "Pattern: Server-side proxy for Test Dispatcher — fixture lives in ghana_cap_app.py adjacent to its single consumer; API key never reaches the browser."

requirements-completed:
  - REQ-react-vite-frontend
  - REQ-flask-json-api-only
  - REQ-tailwind-glassmorphic-system

duration: 12min
completed: 2026-05-09
---

# Phase 04 Plan 01: Foundation (Vite + React + TS + Tailwind v4 + Flask SPA-serve) Summary

**React 19 + Vite 6.3 + TypeScript 5.8 (SWC) + Tailwind v4 SPA scaffold under frontend/, with Flask serving dist/index.html at / and three new JSON endpoints (/api/v1/me, /api/v1/alerts, /api/v1/dispatcher/test) — the foundation Plans 02-05 layer on top of.**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-05-09T19:37:00Z
- **Completed:** 2026-05-09T19:50:00Z
- **Tasks:** 2
- **Files created:** 14 (under frontend/)
- **Files modified:** 4 (.gitignore, .env.example, ghana_cap_app.py, tests/test_endpoints.py)

## Accomplishments

- Vite + React 19 + TS + Tailwind v4 toolchain compiles cleanly: `npm run build` exits 0; emits `frontend/dist/index.html` (1.28 kB), `assets/index-*.css` (7.34 kB), `assets/index-*.js` (194.93 kB; 61 kB gzip).
- Tailwind v4 CSS-first theme ports the dashboard's `:root` + `[data-theme="light"]` blocks verbatim — visual parity with the existing dashboard is preserved at the variable level.
- Flask `dashboard()` route now serves the Vite build SPA shell instead of Jinja; `/assets/<path:filename>` serves hashed bundles. Login flow is unchanged (still Jinja + CSRF).
- Three new JSON endpoints — `/api/v1/me`, `/api/v1/alerts`, `/api/v1/dispatcher/test` — are wired with the existing `@csrf.exempt + @login_required` pattern. The alert list endpoint stringifies `_id` (Pitfall #3) and degrades gracefully on Mongo failure (CLAUDE.md invariant).
- Test Dispatcher endpoint is server-side: the GMeT API key never reaches the browser; the mock payload travels through `process_alert_logic` at `workflow_stage=3` so it traces the full dispatch path and surfaces in Pipeline via Socket.IO `new_alert`.
- 11 new pytest tests cover the SPA-serve route, all three JSON endpoints (login-required + happy path + role gating), and an asset-serve smoke test that skips cleanly if `frontend/dist` is absent.
- 37 / 37 tests pass (26 prior + 11 new). No regressions to Phase 1/2/6/8 contracts.

## Task Commits

Each task was committed atomically:

1. **Task 1: Scaffold Vite + React + TS + Tailwind v4 under frontend/** — `b632645` (feat)
2. **Task 2: SPA serve + 3 JSON endpoints + 11 tests + .env.example update** — `e227e97` (feat)

**Plan metadata:** (commit pending — added in finalization step)

## Files Created/Modified

**Created (frontend/):**
- `frontend/package.json` — Vite manifest with React 19, TS 5.8, Tailwind v4, motion, socket.io-client, leaflet + leaflet-draw, lucide-react, clsx, tailwind-merge, class-variance-authority. Notably does NOT include react-leaflet.
- `frontend/package-lock.json` — locked dependency tree (4161 lines).
- `frontend/vite.config.ts` — Vite plugins (react-swc, tailwindcss); proxies `/api`, `/socket.io` (ws:true), `/static`; build outDir=dist, sourcemap:false.
- `frontend/tsconfig.json` + `tsconfig.app.json` + `tsconfig.node.json` — standard create-vite@6 React-TS config (verbatimModuleSyntax true, jsx react-jsx, strict).
- `frontend/index.html` — Vite entry HTML with Inter + JetBrains Mono Google Font preconnects + no-flash theme bootstrap script setting `data-theme` on `<html>` and `<body>` before React mounts.
- `frontend/src/main.tsx` — `createRoot(document.getElementById('root')!).render(<StrictMode><App /></StrictMode>)` plus the `./index.css` import that triggers Tailwind processing.
- `frontend/src/App.tsx` — minimal placeholder (`<div className="glass-card">GHANA CAP</div>`) to prove the stack works end-to-end. Plans 02-05 replace this.
- `frontend/src/index.css` — Tailwind v4 CSS-first config: `@import "tailwindcss"`, `@custom-variant dark (...)`, `@theme {...}` block (hex values verbatim from ghana_cap_dashboard.html:13-31), `[data-theme="light"]` overrides, three `@utility` rules (`glass-card`, `glass-navbar`, `glass-item`).
- `frontend/src/vite-env.d.ts` — Vite client type reference.
- `frontend/.gitignore` — covers `node_modules`, `dist`, `.vite`, `*.local`.
- `frontend/eslint.config.js` + `README.md` — standard create-vite scaffold output, kept as-is.

**Modified (root):**
- `.gitignore` — appended `frontend/node_modules/`, `frontend/dist/`, `frontend/.vite/` (ensures CI/checked-in repo state stays clean).
- `.env.example` — appended Phase 4 frontend section documenting that `ALLOWED_ORIGINS` already covers Vite dev origin and that `VITE_*` vars must not contain secrets.
- `ghana_cap_app.py`:
  - Added `send_from_directory` to flask import.
  - Added `FRONTEND_DIST` constant before `app = Flask(__name__)`.
  - Rewrote `dashboard()` to `send_from_directory(FRONTEND_DIST, 'index.html')` (kept `@login_required`).
  - Added `frontend_assets()` route at `/assets/<path:filename>`.
  - Added `me()` (`/api/v1/me`), `list_alerts()` (`/api/v1/alerts`), `dispatcher_test()` (`/api/v1/dispatcher/test`).
  - Added `_TEST_DISPATCHER_MOCK_PAYLOAD` fixture adjacent to `dispatcher_test()`.
- `tests/test_endpoints.py` — appended 11 new tests in a Phase 4 section.

## Endpoint Contract (for Plans 02-05)

| Method | Path | Auth | Response | Notes |
|--------|------|------|----------|-------|
| GET | `/` | login_required | 200 + Vite SPA HTML; 302 to `/login` if unauthed | dashboard() now serves frontend/dist/index.html |
| GET | `/assets/<path:filename>` | public | 200 + asset bytes | Hashed Vite bundles |
| GET | `/login` | public | 200 + Jinja login.html | Unchanged from Phase 2 |
| GET | `/api/v1/me` | login_required | 200 `{staff_id, name, agency, role, email}`; 302 if unauthed | Mirrors `session['user']` |
| GET | `/api/v1/alerts` | login_required | 200 `{alerts: [...], degraded: bool}`; 302 if unauthed | `_id` stringified; degrades gracefully on Mongo failure |
| POST | `/api/v1/dispatcher/test` | login_required + Admin role | 201 `{status, identifier, message}`; 403 if non-Admin; 302 if unauthed | Server-side proxy with `_TEST_DISPATCHER_MOCK_PAYLOAD` |

CSRF: all three new JSON endpoints retain `@csrf.exempt` per RESEARCH.md A1 (SameSite=Lax + login_required is the v1 CSRF posture).

## Build Baseline (for Plan 04 size monitoring per RESEARCH.md A4)

| File | Bytes | Gzip |
|------|-------|------|
| dist/index.html | 1,284 | 0.65 kB |
| dist/assets/index-*.css | 7,341 | 2.31 kB |
| dist/assets/index-*.js | 194,934 | 61.05 kB |
| dist/vite.svg | 1,497 | — |
| **Total** | **205,056 (≈208 KB)** | |

Cold build time: 887 ms. 29 modules transformed.

## Decisions Made

- **`create-vite@6` instead of `create-vite@latest`.** `create-vite@9.0.6` (current latest) silently ignores `--template react-swc-ts` and emits a vanilla TS-only scaffold (no React deps, `main.ts` instead of `main.tsx`). RESEARCH.md A3 already flagged 6.x vs 8.x ambiguity; v9 is the third broken bump in this lineage. Pinned to v6.5.0 which is the last version that respects the React-SWC-TS template flag.
- **Accepted registry version drift.** RESEARCH.md baseline was Vite 6.0.3 / TS 5.9.3 / React 19.2.6; create-vite@6 resolved Vite 6.3.5 / TS 5.8.3 / React 19.1.x. Plan explicitly permits this drift; the tighter pins were aspirational, not load-bearing. The build works, all tests pass, and Phase 4's plans 02-05 don't depend on patch-level differences.
- **Cleaned up scaffold cruft (App.css, src/assets/react.svg).** The placeholder App.tsx doesn't reference them; leaving them in would mislead Plan 02 into thinking they're load-bearing. Standard hygiene.
- **Kept eslint.config.js + README.md from the scaffold.** They're idiomatic Vite output, harmless, and Plans 02-05 may use ESLint. The plan's `files_modified` list doesn't enumerate them but doesn't exclude them either.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocker] `create-vite@latest` (v9.0.6) silently ignores `--template react-swc-ts`**
- **Found during:** Task 1 (initial scaffold).
- **Issue:** The plan's exact command — `npm create vite@latest frontend -- --template react-swc-ts -y` — produced a `package.json` with only `typescript` and `vite` (no React, no `@vitejs/plugin-react-swc`) and a `src/main.ts` (vanilla TS, not `main.tsx`). The template flag was silently dropped. This is a regression in `create-vite@9` that the plan author couldn't have known about (RESEARCH.md was authored on 2026-05-09 against a 6.x scaffolder).
- **Fix:** Pinned to `create-vite@6` via `npm create vite@6 -- frontend --template react-swc-ts -y`. v6.5.0 produced a proper React+TS+SWC scaffold (React 19.1, Vite 6.3, TS 5.8). All deps and build steps then proceeded as planned.
- **Files modified:** none beyond plan scope (the scaffolder version is a transient invocation, not a file).
- **Verification:** `cat frontend/package.json` shows `react@^19.1.0`, `react-dom@^19.1.0`, `@vitejs/plugin-react-swc@^3.9.0`, `vite@^6.3.5`. `npm run build` exits 0.
- **Committed in:** b632645 (Task 1 commit).

**2. [Rule 1 - Cleanup] Removed scaffold artifacts unreferenced by the new App.tsx**
- **Found during:** Task 1 (after replacing App.tsx and main.tsx).
- **Issue:** The scaffold ships `src/App.css` (Vite logo styles) and `src/assets/react.svg` which the placeholder `<div className="glass-card">GHANA CAP</div>` no longer references. Leaving them would (a) trick Plan 02 into thinking they're load-bearing and (b) waste 2-3 KB of tracked bytes for nothing.
- **Fix:** `rm -f frontend/src/App.css frontend/src/assets/react.svg && rmdir frontend/src/assets`.
- **Files modified:** none (deletions of just-scaffolded files before commit).
- **Verification:** `ls frontend/src/` shows only `App.tsx`, `index.css`, `main.tsx`, `vite-env.d.ts`. Build still succeeds.
- **Committed in:** b632645 (Task 1 commit; deletions never reached git, since these files were never staged).

**3. [Rule 3 - Blocker fix] Added `.vite` to `frontend/.gitignore`**
- **Found during:** Task 1 (verifying .gitignore coverage).
- **Issue:** The auto-generated `frontend/.gitignore` covered `node_modules`, `dist`, `dist-ssr`, and `*.local` but did NOT cover `.vite/` (Vite's dependency-prebundle cache). The plan's done criteria require it.
- **Fix:** Added a `.vite` line between `dist-ssr` and `*.local`.
- **Files modified:** `frontend/.gitignore`.
- **Verification:** `git check-ignore frontend/.vite/` returns the path (ignored).
- **Committed in:** b632645 (Task 1 commit).

---

**Total deviations:** 3 auto-fixed (1 blocker for the scaffolder bug, 1 cleanup, 1 blocker for gitignore coverage)
**Impact on plan:** All three fixes were minor and necessary. The `create-vite@6` pin is the only one with downstream relevance — Plans 02-05 should also use `create-vite@6` if any sub-scaffolding is ever needed.

## Threat Flags

None. The plan's `<threat_model>` covered all surfaces this plan touches: T-04-01 (login_required) verified by `test_*_requires_login`; T-04-03 (Admin-only Test Dispatcher) verified by `test_dispatcher_test_admin_only`; T-04-04 (`_id` stringification) verified by `test_alerts_list_returns_envelope`; T-04-05 (sourcemap:false) verified in vite.config.ts; T-04-06 (graceful Mongo degradation) implemented in list_alerts(); T-04-07 (server-side proxy) verified by Test Dispatcher having no API-key surface in HTTP request shape; T-04-08 (CORS unchanged) verified by `localhost:5173` still in line 76; T-04-09 (path traversal) inherent to send_from_directory.

## Issues Encountered

**`create-vite@9.0.6` template-flag regression** — see Deviation #1. This burned ~3 minutes of Task 1 (one re-scaffold attempt before pinning to v6). Future executors of this plan should skip directly to `create-vite@6`.

## User Setup Required

None. All Phase 4 frontend env vars are documented as optional in `.env.example`; the existing `ALLOWED_ORIGINS` default already covers the Vite dev origin (`localhost:5173`).

## Next Phase Readiness

- **Plan 04-02 (next):** ready to consume the SPA shell — `frontend/src/App.tsx` is the placeholder it will replace with the real Navbar + Tabs layout. The endpoint contract above is the source of truth.
- **Plans 04-03, 04-04, 04-05:** all unblocked; the toolchain compiles, the JSON contract is fixed, and Tailwind utilities (`glass-card`, `glass-navbar`, `glass-item`) are available.
- **Phase 5 (Map UX):** map deps (`leaflet`, `leaflet-draw`, `@types/leaflet`, `@types/leaflet-draw`) are already installed; the planned Mapbox swap stays local because `react-leaflet` was deliberately not installed.

## Self-Check: PASSED

**Files verified to exist:**
- frontend/package.json — FOUND
- frontend/vite.config.ts — FOUND
- frontend/index.html — FOUND
- frontend/src/index.css — FOUND
- frontend/src/main.tsx — FOUND
- frontend/src/App.tsx — FOUND
- frontend/dist/index.html — FOUND
- frontend/dist/assets/index-DyxBBk9X.js — FOUND
- frontend/dist/assets/index-DE9JaGnF.css — FOUND
- ghana_cap_app.py — FOUND (modified)
- tests/test_endpoints.py — FOUND (modified, +11 tests)
- .env.example — FOUND (modified, +Phase 4 section)

**Commits verified:**
- b632645 — FOUND (Task 1: feat scaffold)
- e227e97 — FOUND (Task 2: feat endpoints + tests)

**Verification commands:**
- `cd frontend && npm run build` — exits 0, emits dist/index.html + dist/assets/index-*.{js,css}
- `pytest tests/ -q` — 37 passed, 0 failed
- `grep -c "@csrf.exempt" ghana_cap_app.py` — 8 (5 prior + 3 new)
- `grep -n "localhost:5173" ghana_cap_app.py` — line 76 unchanged
- `python -c "import os, sys; sys.exit(0 if not os.path.exists('frontend/tailwind.config.js') else 1)"` — exits 0 (no v3 config artifact)
- `grep -n "sourcemap: false" frontend/vite.config.ts` — line 23 confirmed

---
*Phase: 04-frontend-migration-to-react-vite-typescript-tailwind-framer-*
*Plan: 01*
*Completed: 2026-05-09*
