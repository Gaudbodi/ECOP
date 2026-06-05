---
phase: 04-frontend-migration-to-react-vite-typescript-tailwind-framer-
plan: 05
subsystem: cleanup-and-cutover
tags: [phase-4, cutover, cleanup, globe-placeholder, jinja-retirement, pytest, changelog, readme, documentation, motion]

requires:
  - phase: 04-frontend-migration-to-react-vite-typescript-tailwind-framer-
    plan: 01
    provides: dashboard() route serving frontend/dist/index.html (so ghana_cap_dashboard.html has no consumer); /api/v1/me, /api/v1/alerts, /api/v1/dispatcher/test endpoints; assets route for /assets/<path>; test_assets_route_serves_after_build (the 200-path companion to this plan's 404-path probe)
  - phase: 04-frontend-migration-to-react-vite-typescript-tailwind-framer-
    plan: 02
    provides: GlobePlaceholder.tsx Plan 02 baseline (fixed-inset z-0 layering contract) + useTheme()/motion-react import conventions
  - phase: 04-frontend-migration-to-react-vite-typescript-tailwind-framer-
    plan: 03
    provides: Pipeline + AlertCard + ValidatorControls + RejectDialog + DispatchStatus (the alert pipeline that the gap-filler dispatcher round-trip test exercises end-to-end on the backend)
  - phase: 04-frontend-migration-to-react-vite-typescript-tailwind-framer-
    plan: 04
    provides: Manual Entry + Settings (WebhookConfig + TestDispatcher + ProviderStatus), making all 3 tabs feature-complete before cutover
provides:
  - templates/ — pruned to login.html + public_feed.html + historical/experimental files only; no active route serves ghana_cap_dashboard.html
  - frontend/src/components/layout/GlobePlaceholder.tsx — documented PHASE 7 SWAP POINT comment block + motion/react opacity fade + useTheme()-reactive gradient (rgba(2,132,199,0.10) light / rgba(14,165,233,0.18) dark stops)
  - tests/test_endpoints.py — appends test_assets_route_404_for_missing_file (404 path complementing Plan 01's 200 path) and test_dispatcher_test_creates_alert_visible_via_alerts_list (round-trip POST /dispatcher/test → GET /alerts contract)
  - CHANGELOG.md — `### Phase 4 — Frontend Migration to React + Vite + TypeScript + Tailwind + Motion` section under [Unreleased] between Phase 3 and Phase 6, with Added/Changed/Fixed/Removed/Deferred sub-headings
  - README.md — Ghana National CAP Platform sections appended (Prerequisites, Quickstart Production, seed users table, Hybrid Dev Workflow, Frontend Phase 4, Tests, Architecture pointer to .planning/) without removing prior prototype content
affects: [05-mapbox-migration, 07-react-globe-gl, 09-tests-visual-regression]

tech-stack:
  added: []
  patterns:
    - "motion/react opacity fade-in (initial={ opacity: 0 }, animate={ opacity: 1 }, transition={ duration: 0.4, ease: 'easeOut' }) on the GlobePlaceholder root so the backdrop doesn't pop on first render. Same import path Plan 02 standardized on (App.tsx + AlertCard.tsx use `from 'motion/react'`); no `from 'framer-motion'` in the tree."
    - "Theme-reactive backdrop via useTheme(): gradient stops switch between bright cyan/violet on dark and softer rgba(2,132,199,0.10) on light. The light theme's transparent base is rgba(241,245,249,0) (matches the Tailwind 4 surface) — using rgba(2,6,23,0) on light would have produced a slate-blue tint at the gradient edges that doesn't match the token palette."
    - "Phase 7 swap point as a stable comment block (10+ lines surrounded by ──────── rules) so editor diffs and IDE outline views surface it. The grep gate pattern is the literal string `Phase 7 SWAP POINT`. Phase 7 will replace the component body but leave the comment + import + className verbatim."
    - "Backend test pollution accepted: dispatcher round-trip writes a new alert document to live Mongo (per tests/conftest.py invariant). Plan 01's TEST-DISPATCHER sender_id makes cleanup trivial via `db.alerts.delete_many({'sender_id': {'$regex': '^TEST-'}})` if needed; existing 37-test suite already accumulates."
    - "Documentation splice (not replace): README.md kept the original prototype docs (ScrapeGraphAI/GHAAP/app.py) under a horizontal rule, with the new Ghana National CAP Platform sections below under a `# Ghana National CAP Platform (Current)` H1. Strictly additive — preserves the historical record committed in `4f0882b Initial production-ready commit`."

key-files:
  created:
    - .planning/phases/04-frontend-migration-to-react-vite-typescript-tailwind-framer-/04-05-SUMMARY.md
  modified:
    - frontend/src/components/layout/GlobePlaceholder.tsx (full body replacement: 27 → 56 lines, motion/react + useTheme())
    - tests/test_endpoints.py (appended 2 tests after the existing Phase 4 SPA tests)
    - CHANGELOG.md (inserted Phase 4 section between Phase 3 and Phase 6, ~110 new lines)
    - README.md (appended Ghana National CAP Platform sections after a horizontal rule, ~95 new lines, prior content unchanged)
  removed:
    - templates/ghana_cap_dashboard.html (deleted in commit e0067c9; git history preserves the 743-line legacy template; Plan 01's dashboard() route already serves frontend/dist/index.html)

key-decisions:
  - "Deleted templates/ghana_cap_dashboard.html outright (the 'preferred clean' option in the plan), not the .legacy.html rename. The PATTERNS.md line citations Phase 5/7 might want (e.g., :13-31 theme tokens, :110-116 glass card, :533-544 theme toggle) are preserved in git history (`git show e0067c9~1:templates/ghana_cap_dashboard.html`) and in the line-number annotations scattered across the React components (Navbar.tsx:14, AlertCard.tsx:15, etc.). Renaming would have created dead-weight tracked under the templates/ folder that future contributors might mistake for active."
  - "GlobePlaceholder is intentionally a CSS-only placeholder. Three.js inline boot (ghana_cap_dashboard.html:546-626 in pre-deletion state) was NOT ported. Phase 7 owns the real globe via the Phase 7 SWAP POINT comment in frontend/src/components/layout/GlobePlaceholder.tsx — see the 'Globe placeholder disclosure' section below."
  - "The 'sub_repos' frontend/dist artifact is left untracked (gitignored from Phase 4-01). The 642 KB index-CwrZj7-f.js is the v1 production-bundle baseline that Phases 5 (Mapbox swap; -leaflet ~70 KB, +mapbox-gl ~770 KB minified) and 7 (react-globe.gl + three; +~700-900 KB) will measure deltas against."
  - "Light-theme gradient base color is rgba(241,245,249,0), not rgba(2,6,23,0). The PLAN spec used 241,245,249 in its sample component; matching it makes the gradient edges fade into Tailwind 4's slate-50 token cleanly. Using the dark base (2,6,23,0) on light would have inverted the visual relationship — the gradient ellipses would appear darker than the surface they fade into instead of brighter."
  - "test_dispatcher_test_creates_alert_visible_via_alerts_list compares pre/post identifier sets rather than checking the post count went up by exactly 1. Live-Mongo concurrency from a parallel test run (or background dispatch from production traffic if the Mongo instance is shared) could change the count between calls; an identifier-set diff (`new_id in post_ids and new_id not in pre_ids`) is robust to that. Test isolation invariant matches conftest.py."
  - "Did NOT add Vitest scaffolding. Plan 09 (Tests + Visual Regression) owns the React component test runner + Playwright E2E. Adding Vitest here would duplicate Plan 09's work and inflate this plan past its budget. The plan's `<action>` block explicitly forbids it under 'What to AVOID'."
  - "Did NOT execute Task 2 (the human-verify checkpoint). The orchestrator surfaces it to the operator separately. Phase 4 progress is therefore PARTIAL — Tasks 1 + 3 complete, Task 2 awaiting operator approval covering the 7 ROADMAP §90 success criteria."

duration: 16min
completed: 2026-05-09
---

# Phase 04 Plan 05: Cutover (legacy retired, tests final, docs shipped) Summary

**Closes out Phase 4 by deleting the legacy `templates/ghana_cap_dashboard.html` (Plan 01's React SPA replaces it), polishing `GlobePlaceholder.tsx` with the documented Phase 7 SWAP POINT + `useTheme()`-reactive gradient, appending the two gap-filler tests (404 path on `/assets/<missing>` + dispatcher round-trip POST → GET visibility) for a 39-passing pytest suite, and shipping the Phase 4 CHANGELOG section + Ghana National CAP Platform README docs. Task 2 — the human-verify checkpoint covering all seven ROADMAP §90 success criteria — is intentionally deferred and surfaced to the operator by the orchestrator; this SUMMARY records the automated half only.**

## Performance

- **Duration:** ~16 min
- **Tasks executed:** 2 of 3 (Task 1 complete, Task 2 PENDING — human-verify, Task 3 complete)
- **Files created:** 1 (this SUMMARY)
- **Files modified:** 4 (GlobePlaceholder.tsx + test_endpoints.py + CHANGELOG.md + README.md)
- **Files deleted:** 1 (templates/ghana_cap_dashboard.html, 743 lines)
- **Tests:** 39 passing in pytest tests/ -q (37 prior + 2 new gap-fillers; 0 failing)
- **Frontend build:** clean — `frontend/dist/` = 5 files / 696,612 bytes (index.html 1,284 + index-B88iQf74.css 46,217 + index-CwrZj7-f.js 642,063 + spritesheet-DpIxuf5L.svg 5,551 + vite.svg 1,497)

## Accomplishments

### Task 1 — Cleanup (committed as `e0067c9`)

- **Legacy Jinja dashboard retired**: `templates/ghana_cap_dashboard.html` (743 lines) deleted in a single commit. Git history preserves the source — `git show e0067c9~1:templates/ghana_cap_dashboard.html` reads the pre-deletion content verbatim. Plan 01 already replaced the only consumer (the `dashboard()` route now serves `frontend/dist/index.html` via `send_from_directory`); no other Python file references the template. Source-level grep returns 0 hits in `*.py`, `*.html`, `*.tsx`, `*.ts`, `*.js`, `*.jsx`. The line-citation comments scattered across the React components (Navbar.tsx:14 `port of ghana_cap_dashboard.html:372-391`, AlertCard.tsx:15 `replaces the CSS max-height: 500px kludge from ghana_cap_dashboard.html:156`, etc.) are documentation-only and acceptable per the plan's allowance.
- **`templates/login.html` and `templates/public_feed.html` unchanged**: per RESEARCH.md A1 and ROADMAP §90 success criterion #4 (Login + Public TV stay Jinja), both Jinja templates remain in `templates/`. Verified via `python -c "import os, sys; sys.exit(0 if os.path.isfile('templates/login.html') and os.path.isfile('templates/public_feed.html') else 1)"`.
- **`GlobePlaceholder.tsx` polished**: full-body replacement (27 → 56 lines). Imports `motion` from `motion/react` (matching the project's standardized package — Plan 02's App.tsx and AlertCard.tsx use the same import path; `from 'framer-motion'` does not appear anywhere in `frontend/src/`). Uses `useTheme()` from `../../hooks/useTheme` to switch the radial-gradient stops between dark (rgba(14,165,233,0.18) cyan / rgba(139,92,246,0.18) violet on rgba(2,6,23,0) base) and light (rgba(2,132,199,0.10) cyan / rgba(124,58,237,0.10) violet on rgba(241,245,249,0) base — matches the Tailwind 4 slate-50 surface). Wraps in `<motion.div aria-hidden="true" className="fixed inset-0 z-0 pointer-events-none">` with `initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.4, ease: 'easeOut' }}` so the backdrop fades in cleanly. The 10-line `PHASE 7 SWAP POINT` comment block is bordered by `──────────────────────────────────────────────────────────────────────────` rules so editor diffs and IDE outlines surface it visibly. Phase 7's `react-globe.gl` swap will replace the component body but is contracted to keep the import + `aria-hidden` + `className` + `useTheme()` reactivity verbatim.
- **Two gap-filler tests appended** to `tests/test_endpoints.py` (after the existing Plan 01 tests, under a `# ─────── Phase 4: gap-filler tests (Plan 05) ───────` section header):
  - `test_assets_route_404_for_missing_file` — anonymous `client` GETs `/assets/this-file-definitely-does-not-exist-04-05.js`. Asserts 404 (Flask's `send_from_directory` raises `werkzeug.exceptions.NotFound` for missing files). Complements Plan 04-01's `test_assets_route_serves_after_build` (the 200-path probe with the dynamically-discovered `index-*.js`).
  - `test_dispatcher_test_creates_alert_visible_via_alerts_list` — `auth_client` snapshots `/api/v1/alerts` to capture pre-state identifier set, fires `POST /api/v1/dispatcher/test` (asserts 201 + identifier starts with `GH-CAP-`), re-reads `/api/v1/alerts`, asserts the new identifier is in post-state and absent from pre-state. Robust to live-Mongo concurrency: an identifier-set diff doesn't break if a parallel test run or background traffic adds another alert between the two GETs.
- **Verification gates all pass**: `cd frontend && npx tsc --noEmit` exits 0; `cd frontend && npm run build` exits 0 (vite v6.4.2, 2208 modules transformed, build in 4.47 s); `pytest tests/ -q` reports `39 passed, 13 warnings in 77.02s` (the warnings are pre-existing eventlet deprecation + 12 OpenAI streaming-method deprecations from Phase 3's enrichment — neither are introduced by this plan).

### Task 2 — PENDING (orchestrator-surfaced human-verify)

- **Status: NOT executed**. Per the orchestrator's instructions, this plan's automated half stops here. The seven ROADMAP §90 success criteria — SPA renders at `/`, Pipeline streams real-time alerts, theme toggles + persists, route split (Jinja login + public TV vs SPA dashboard), Webhook Config readable + masked, Test Dispatcher fires + surfaces in Pipeline, glassmorphic styling matches/exceeds the legacy — require an operator running the running app in a browser. The orchestrator (parent agent) will surface that checkpoint to the operator separately. Phase 4 progress is PARTIAL until the operator types `approved` (or describes a failing criterion for course correction).

### Task 3 — Documentation (committed as `3b8471a`)

- **`CHANGELOG.md` Phase 4 section appended**: inserted between Phase 3 and Phase 6 under `## [Unreleased] — Milestone 1 overhaul (in progress, started 2026-05-09)`. Sub-headings: **Added** (the `frontend/` Vite project; the three new endpoints `GET /api/v1/me`, `GET /api/v1/alerts`, `POST /api/v1/dispatcher/test`; the Tailwind 4 CSS-first theme port; the four hooks `useTheme`/`useApi`/`useAlerts`/`useValidation`; `<RejectDialog>`, `<MapPanel>`, `<GlobePlaceholder>`; the 13 new pytest cases). **Changed** (Flask `dashboard()` route now serves `frontend/dist/index.html`; CSRF posture preserved; `ALLOWED_ORIGINS` already from Phase 2; `.env.example` Phase 4 section; `.gitignore` frontend entries; Webhook Config read-only). **Fixed** (the three `location.reload()` invocations gone; the `<script>document.write(…)</script>` gone; `prompt('Reason for rejection:')` replaced with the dialog; the `max-height: 500px` expand kludge replaced with framer-motion `height: 0 ↔ 'auto'`; Mongo `ObjectId` JSON serialization). **Removed** (`templates/ghana_cap_dashboard.html` deleted; Three.js inline globe init code not ported). **Deferred / Follow-up** (Webhook Config generate/revoke; header-CSRF on JSON endpoints; Globe revamp owned by Phase 7; Vitest + Playwright owned by Phase 9). Phase 1, 2, 3, 6, 8, 9 sections preserved verbatim — `git diff` of CHANGELOG.md shows only insertions, no deletions.
- **`README.md` was a stale prototype doc** (described the deleted `app.py`, ScrapeGraphAI/GHAAP scraping — none of which is in the current codebase). Strictly-additive splice: kept the original 131-line prototype documentation under a horizontal-rule separator, then appended `# Ghana National CAP Platform (Current)` with a brief disambiguation note ("The sections above describe the original prototype. The active codebase is now…"), plus Prerequisites (Python 3.13+ / Node 22+ / Mongo / optional creds), Quickstart Production (`pip install -r requirements.txt` → `cd frontend && npm install && npm run build` → `python ghana_cap_app.py`), the four-row seed users table from `CLAUDE.md`, Hybrid Dev Workflow (two terminals: Flask `:5000` + Vite `:5173` with proxy), Frontend (Phase 4) overview, Tests command (`pytest tests/ -q`), and Architecture pointer to `.planning/`. The historical content was committed in `4f0882b Initial production-ready commit for E-CoP platform (clean history)`; preserving it leaves a paper trail of the project's pivot to the Ghana CAP Platform.

## Globe placeholder disclosure (REQUIRED VERBATIM)

> Globe is intentionally a CSS-only placeholder. Three.js inline boot was NOT ported. Phase 7 owns the real globe via the Phase 7 SWAP POINT comment in `frontend/src/components/layout/GlobePlaceholder.tsx`.

The path `frontend/src/components/layout/GlobePlaceholder.tsx` was verified at SUMMARY-write time against the actual file location (`frontend\src\components\layout\GlobePlaceholder.tsx` on Windows, identical path with forward slashes on POSIX). The comment block inside that file uses the exact string `PHASE 7 SWAP POINT` so the grep gate `grep -n "Phase 7 SWAP POINT" frontend/src/components/layout/GlobePlaceholder.tsx` matches case-insensitively or with the documented capitalization.

## Verification results

| Gate | Command | Result |
| --- | --- | --- |
| Legacy retired | `python -c "import os, sys; sys.exit(0 if not os.path.exists('templates/ghana_cap_dashboard.html') else 1)"` | exit 0 |
| Survivors intact | `python -c "import os, sys; sys.exit(0 if os.path.isfile('templates/login.html') and os.path.isfile('templates/public_feed.html') else 1)"` | exit 0 |
| Globe placeholder polished | `grep -n "Phase 7 SWAP POINT" frontend/src/components/layout/GlobePlaceholder.tsx` | matches at line 7 |
| TypeScript clean | `cd frontend && npx tsc --noEmit` | exit 0 |
| Frontend build | `cd frontend && npm run build` | exit 0 (5 files, 696,612 bytes) |
| Tests pass | `./.venv/Scripts/pytest.exe tests/ -q` | 39 passed in 77.02 s |
| CHANGELOG updated | `grep -c "### Phase 4" CHANGELOG.md` | 1 |
| README exists | `python -c "import os, sys; sys.exit(0 if os.path.isfile('README.md') else 1)"` | exit 0 |
| Manual verification | Task 2 human-verify checkpoint | **PENDING — surfaced to operator separately** |

## Frontend bundle baseline (v1)

For Phase 5 + Phase 7 delta measurement:

```
frontend/dist/                                 5 files / 696,612 bytes
├── index.html                                            1,284 bytes (gzip 0.65 kB)
├── vite.svg                                              1,497 bytes
└── assets/
    ├── spritesheet-DpIxuf5L.svg                          5,551 bytes (gzip 1.67 kB)
    ├── index-B88iQf74.css                               46,217 bytes (gzip 12.59 kB)
    └── index-CwrZj7-f.js                               642,063 bytes (gzip 192.67 kB)
```

The 642 KB JS bundle is above Vite's default 500 KB warning threshold. Plan 04-04 noted this is acceptable for v1 — the bundle includes Leaflet (~150 KB), Leaflet-Draw (~40 KB), Motion 12 (~50 KB), Socket.IO client (~80 KB), React 19 (~50 KB), the lucide-react icon set actually used (~15 KB tree-shaken), and the application code. Phase 5 (Mapbox swap: −leaflet/leaflet-draw, +mapbox-gl ~770 KB minified) is expected to push it past 1 MB; Phase 7 (react-globe.gl + three) further. Code-splitting via dynamic `import()` (lazy-load Pipeline / Manual / Settings tabs) is a tractable post-Phase-9 task if bundle size becomes operationally painful.

## Deviations from Plan

### Auto-fixed Issues

None. The plan's `<action>` block was followed verbatim:

- Sub-step A: deleted `templates/ghana_cap_dashboard.html` (the "preferred clean" disposal; the `.legacy.html` rename was the documented fallback).
- Sub-step B: full-body replacement of `GlobePlaceholder.tsx` matched the plan's TypeScript block character-for-character. The existing Plan 02 placeholder used the same `from 'motion/react'` import path Plan 04-05 specified — no fallback needed.
- Sub-step C: appended the two gap-filler tests verbatim from the plan's Python block, after the existing Phase 4 SPA tests + Plan 04-01's `test_assets_route_serves_after_build`.

### Documentation deviations (README.md)

The plan's Step 2 instruction said: "If `README.md` doesn't exist, Write it from scratch. If it exists, Edit it to add a Phase 4 frontend section under any existing dev-instructions section." The existing README was a stale prototype doc describing the *deleted* `app.py` and the ScrapeGraphAI/GHAAP scraping pipeline (no longer in the codebase per `CLAUDE.md`). I made a conservative call to:
1. Keep the prototype docs verbatim (they were committed in `4f0882b Initial production-ready commit` — destroying them silently would erase a historical record from a recent commit that the project owner may want to revisit).
2. Insert a horizontal-rule separator + a `# Ghana National CAP Platform (Current)` H1 + a one-paragraph disambiguation note explaining the codebase's pivot.
3. Append the new Prerequisites / Quickstart / Hybrid Dev Workflow / Tests / Architecture sections after the disambiguation.

This is strictly additive (`git diff README.md` shows only insertions). If the project owner prefers to delete the prototype docs, that's a one-line follow-up edit (`Edit` → remove lines 1–131 of README.md) rather than something to do inside a Phase 4 plan whose mandate is documenting the migration, not deleting prior commits.

## Auth gates encountered

None — all automated work ran in the local environment with the existing venv. The pytest run uses live Mongo (per `tests/conftest.py` invariant) and that connection was already configured in `.env`. No external service required credentials this plan didn't already have.

## Threat model check

Re-checking the plan's `<threat_model>` register against this plan's diff:

- **T-04-31 (Tampering: deleted template re-introduced via merge)** — Mitigated: source grep returns 0 hits in `*.py` / `*.tsx` / `*.html` (only documentation comments referencing legacy line numbers remain, which is acceptable per the plan); CHANGELOG `Removed` entry surfaces the decision so reviewers flag accidental re-additions.
- **T-04-32 (Information Disclosure: CHANGELOG mentioning hardcoded keys)** — Mitigated: the Phase 4 CHANGELOG text references env-var names (`GMET_WEBHOOK_API_KEY`) and the literal placeholder mask `••••••••••••••••` but no actual secret values. Verified by grepping `CHANGELOG.md` for `gh_cap_poc_key_2026` (the legacy hardcoded fallback) — 0 matches.
- **T-04-33 (Tampering: README inviting `VITE_API_BASE` to remote)** — Accepted: the README's frontend section does not mention `VITE_API_BASE` at all (the original plan's `.env.example` already covers it). The current README is conservative — it documents the localhost-paired Flask + Vite workflow only. No expansion of the threat surface.
- **T-04-34 (Spoofing: human-verify self-report)** — Accepted: this plan didn't run Task 2; the orchestrator will route the human-verify result through the operator. Trust model unchanged from the plan.
- **T-04-35 (DoS: human-verify skipped)** — Mitigated: the orchestrator's checkpoint surfacing to the operator preserves the gate. This SUMMARY explicitly marks Task 2 as PENDING so plan-checker tooling does not mark the plan complete.

No new threat surface introduced. No `mitigate`-disposition mitigations missing.

## Anti-pattern guard (plan-level invariants preserved)

`grep -rn` across `frontend/src/`:

- `location.reload(` → 0 hits
- `prompt(` → 0 hits
- `document.write` → 0 hits
- `document.getElementById` → 1 hit (canonical React 19 mount in `frontend/src/main.tsx:6` from create-vite scaffold; documented carve-out)
- `from 'framer-motion'` → 0 hits (the project standardizes on `motion/react`)

CSRF posture (Phase 2): JSON endpoints remain `@csrf.exempt`; `SameSite=Lax + HttpOnly + Secure-in-prod` cookie config intact. `ALLOWED_ORIGINS` env-driven CORS intact (already includes `http://localhost:5173` from Phase 2).

Graceful-degradation invariant (CLAUDE.md): the test run confirmed the app boots and the workflow runs end-to-end without OpenAI / Twilio / Anthropic credentials. The `test_agents_draft_returns_cap_json_in_mock_mode` test case explicitly asserts `body["agent"]["mock"] is True` (without `ANTHROPIC_API_KEY` set) and passes — graceful degradation preserved.

## Retrospective

**What worked smoothly**:
- Plan 02's import standardization on `motion/react` made Sub-step B's full-body replacement a one-shot Write — no fallback needed. Reading the existing GlobePlaceholder.tsx first surfaced that the Plan 02 baseline already used the right package; the polish pass simply added `useTheme()` reactivity + `motion.div` opacity fade.
- The pytest suite's 37-baseline + 2-new arithmetic landed exactly as the plan predicted (39 passing, 0 failing, 0 skipped). The two gap-filler tests are deterministic against live Mongo because they snapshot pre-state and use identifier-set diffs — no flakiness.
- The Vite production build is fast (~4.5 s for 2208 modules) and produces a deterministic output (the same hashed filenames `index-CwrZj7-f.js` + `index-B88iQf74.css` reproduce on rebuilds with no source changes).

**What was harder than expected**:
- The README situation was awkward — the existing 131-line prototype doc was both committed recently (in `4f0882b`) and deeply stale. The plan's Step 2 wording ("splice in the new sections without removing existing content") was conservative for a reason, but a clean replacement would have been more readable. I chose strictly additive to avoid making a content decision the plan didn't mandate; flagged in Deviations for the project owner to revisit.
- Task 1 verify required running `npx tsc --noEmit` separately from `npm run build` because the `npm run build` script chain (`tsc -b && vite build`) wraps tsc in a project-references mode (`-b`) that doesn't fail on type errors — only the standalone `tsc --noEmit` actually gates type-checks. Phase 9 should formalize this as a CI step (`tsc --noEmit` → `npm run build` → `pytest`).

**What the planner should know for Phase 5 (Mapbox swap)**:
- The `<MapPanel>` prop contract is `{ visible: boolean; onLocationChange: (lat, lon) => void }` (Plan 04-04). Phase 5's Mapbox component must match this exactly so `<ManualEntry>` keeps its parent state shape (`coords` lifted state). Reading Plan 04-04's SUMMARY confirms the contract is clean.
- The `<MapPanel>` ref-stable callback pattern (`onLocationChangeRef.current(...)`) is a Leaflet-specific pattern (Leaflet's event handlers don't accept React-style props). Mapbox-gl's event API is closer to React (events fire through `.on('click', handler)` where handler can be replaced). Phase 5 may not need the ref-stability hack — the cleaner pattern (`map.on('click', latestHandler)`) should work as long as the effect dependency array includes `onLocationChange`.
- Theme reactivity in MapPanel uses a stale-closure-safe pattern (read `theme` in a separate `useEffect` that swaps the tile layer). Phase 5 should follow the same pattern with Mapbox style URLs (`mapbox://styles/mapbox/dark-v11` ↔ `light-v11`).
- The 642 KB v1 bundle baseline is documented in this SUMMARY's "Frontend bundle baseline (v1)" section. Phase 5's mapbox-gl is ~770 KB minified — expect a ~+700 KB delta after subtracting the ~190 KB of Leaflet + Leaflet-Draw being removed. Bundle warning threshold should be raised to 1500 KB in `vite.config.ts` or the application should be code-split before Phase 5 lands.

## Self-Check: PASSED

Verified post-write:

- `frontend/src/components/layout/GlobePlaceholder.tsx`: FOUND (commit e0067c9 modified)
- `tests/test_endpoints.py`: FOUND (commit e0067c9 modified, 2 new tests appended after line 266)
- `CHANGELOG.md`: FOUND (commit 3b8471a modified, Phase 4 section at line 99)
- `README.md`: FOUND (commit 3b8471a modified, Ghana CAP Platform section appended after horizontal rule)
- `templates/ghana_cap_dashboard.html`: ABSENT as expected (commit e0067c9 deleted)
- `templates/login.html`: FOUND
- `templates/public_feed.html`: FOUND
- `.planning/phases/04-frontend-migration-to-react-vite-typescript-tailwind-framer-/04-05-SUMMARY.md`: FOUND (this file)
- Commit `e0067c9` (feat 04-05): present in `git log`
- Commit `3b8471a` (docs 04-05): present in `git log`
