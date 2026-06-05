---
phase: 04-frontend-migration-to-react-vite-typescript-tailwind-framer-
plan: 02
subsystem: ui
tags: [react, typescript, tailwindcss-v4, motion, framer-motion, lucide-react, socket.io-client, glassmorphism, theme]

requires:
  - phase: 04-frontend-migration-to-react-vite-typescript-tailwind-framer-
    plan: 01
    provides: Vite + React 19 + TS + Tailwind v4 toolchain; GET /api/v1/me; GET /api/v1/alerts; Socket.IO default namespace
provides:
  - frontend/src/lib/cn.ts — clsx + tailwind-merge class composition utility
  - frontend/src/api/types.ts — CapAlert, User, WorkflowStage, Severity, Urgency, Certainty, Category, CapStatus, CapMsgType, CapScope, Role, AlertsListResponse, ManualAlertRequest, ValidationRequest, DispatchSuccessResponse, ApiErrorResponse, AgentDraftResponse
  - frontend/src/api/client.ts — apiFetch<T>() + ApiError class with /login redirect detection
  - frontend/src/api/socket.ts — typed Socket singleton with ServerToClientEvents (new_alert, alert_updated)
  - frontend/src/hooks/useTheme.ts — {theme, toggle, setTheme} with localStorage.theme persistence + data-theme on <html> + <body>
  - frontend/src/hooks/useApi.ts — generic GET hook returning {data, error, loading, refetch}
  - frontend/src/components/ui/GlassCard.tsx — variant='card'|'navbar'|'item'
  - frontend/src/components/ui/SeverityBadge.tsx — substring-match severity → color
  - frontend/src/components/ui/StageBadge.tsx — WorkflowStage 0/1/3 → red/amber/emerald
  - frontend/src/components/layout/Navbar.tsx — GHANA CAP brand + TabNav + ThemeToggle + user profile + Logout
  - frontend/src/components/layout/ThemeToggle.tsx — lucide Sun/Moon button
  - frontend/src/components/layout/TabNav.tsx — 3-tab nav with role gating (Manual Entry hidden for cap validator)
  - frontend/src/components/layout/GlobePlaceholder.tsx — static radial-gradient backdrop with Phase 7 SWAP POINT marker
  - SPA shell renders at / showing brand + 3 tabs + theme toggle + user name/role + Logout + animated tab transitions
affects: [04-03, 04-04, 04-05]

tech-stack:
  added: []  # All deps already installed in Plan 01 (motion, clsx, tailwind-merge, lucide-react, socket.io-client)
  patterns:
    - "Class composition: cn(...inputs) wrapping clsx + tailwind-merge — single import everywhere"
    - "API client: apiFetch<T>(path, init?) with credentials:'same-origin' + redirect-to-/login detection"
    - "Socket.IO singleton at module scope (RESEARCH.md Pattern 5) — survives StrictMode double-mount because not constructed inside a useEffect"
    - "Theme port: localStorage.theme + data-theme on <html> + <body>; default 'dark'; useEffect sync (matches no-flash bootstrap in index.html)"
    - "GlassCard variant API (3 fixed values) instead of CVA — codebase only has card / navbar / item flavors"
    - "Tab transitions via AnimatePresence mode='wait' + motion.div(key=tab) — duration 0.18s, easeOut, y:8 → y:0 → y:-8"
    - "Skeleton loading state for user profile in Navbar (h-3/w-24 + h-2.5/w-16 animate-pulse) — fall-through to red 'Session expired' on null user"
    - "Role gate is UX-only — server still enforces at ghana_cap_app.py:228-243; matches Jinja gate at ghana_cap_dashboard.html:376"

key-files:
  created:
    - frontend/src/lib/cn.ts
    - frontend/src/api/types.ts
    - frontend/src/api/client.ts
    - frontend/src/api/socket.ts
    - frontend/src/hooks/useTheme.ts
    - frontend/src/hooks/useApi.ts
    - frontend/src/components/ui/GlassCard.tsx
    - frontend/src/components/ui/SeverityBadge.tsx
    - frontend/src/components/ui/StageBadge.tsx
    - frontend/src/components/layout/Navbar.tsx
    - frontend/src/components/layout/ThemeToggle.tsx
    - frontend/src/components/layout/TabNav.tsx
    - frontend/src/components/layout/GlobePlaceholder.tsx
  modified:
    - frontend/src/App.tsx (rewrote placeholder → shell with Navbar + AnimatePresence)

key-decisions:
  - "ApiError uses explicit field declarations rather than constructor parameter properties because tsconfig.app.json:erasableSyntaxOnly:true (TS 5.8+ default in create-vite@6) forbids the `constructor(public foo)` shorthand. Behaviorally identical."
  - "GlassCard takes a small `variant` prop (3 fixed values) rather than reaching for class-variance-authority. PATTERNS.md confirmed only three glass flavors exist; CVA's value emerges with ~5+ variants or compound conditions."
  - "useApi accepts `null` as path to skip fetching. This is the canonical pattern for guarded fetches Plans 03 + 04 will use (e.g., `useApi(user ? `/x/${user.id}` : null)`)."
  - "Tab is local useState<TabId>, not a router, per RESEARCH.md A6. No deep-linkable URLs requirement → router would be premature."
  - "Default theme is 'dark' (matches Jinja default at ghana_cap_dashboard.html:543), not system-preference. Plan key_reminders mentioned system-preference fallback; the existing Jinja behavior is dark-by-default with no media query — keep 1:1 parity. Documented as deviation #1 below."

duration: 6min
completed: 2026-05-09
---

# Phase 04 Plan 02: SPA Shell (Navbar + Tabs + Theme + Glass primitives) Summary

**Replaces the placeholder `App.tsx` from Plan 01 with the full visible React shell — navbar + 3 tabs (Pipeline / Manual Entry / Settings) + theme toggle + animated tab transitions + the shared primitives (`useTheme`, `useApi`, `apiFetch`, `socket`, types, GlassCard / SeverityBadge / StageBadge) that Plans 03 + 04 layer on top of.**

## Performance

- **Duration:** ~6 min
- **Started:** 2026-05-09T19:58:48Z
- **Completed:** 2026-05-09T20:05:20Z
- **Tasks:** 2 (atomic commits)
- **Files created:** 13 (under `frontend/src/{api,hooks,lib,components/{ui,layout}}/`)
- **Files modified:** 1 (`frontend/src/App.tsx` rewrote placeholder → shell)

## Accomplishments

- The shared primitives Plans 03 + 04 will consume are now defined: typed API client + redirect-to-`/login` detection, typed Socket.IO singleton, generic `useApi` hook, theme hook with localStorage persistence + data-theme sync on `<html>` and `<body>`, and a `cn()` utility for class composition.
- The visible shell renders at `/`: brand text "GHANA CAP" with sky→purple gradient, three tabs with role gating (Manual Entry hidden for `cap validator`), lucide Sun/Moon theme toggle, user name + role + agency loaded from `/api/v1/me`, Logout link to `/logout`. Tab transitions animate via `AnimatePresence` mode="wait" + `motion.div` key=tab (opacity + y).
- The `GlassCard` component consolidates the three glass utility variants (`.glass-card`, `.glass-navbar`, `.glass-item`) behind a single `variant` prop. The Navbar uses `variant="navbar"` with `rounded-none` override; the placeholder tab content uses the default `card` variant.
- `SeverityBadge` ports the substring-match logic from `public_feed.html:294-301` verbatim, including the four CAP severity colors (`#b91c1c` Extreme, `#ea580c` Severe, `#ca8a04` Moderate, `#16a34a` Minor) and the sky→purple gradient for unknown / default severities.
- `StageBadge` maps `WorkflowStage` 0 / 1 / 3 to "Draft/Rejected" / "Pending Review" / "Dispatched" with red / amber / emerald variants, matching the colors at `ghana_cap_dashboard.html:189-198`.
- `GlobePlaceholder` is a static radial-gradient backdrop with an explicit `Phase 7 SWAP POINT` comment block flagging where the future `react-globe.gl` instance will plug in (RESEARCH.md Open Question 5; PATTERNS.md "Anti-patterns to NOT Carry Over").
- `npx tsc --noEmit` and `npm run build` both exit 0. `pytest tests/ -q` still 37/37 (no Python touched).

## Component Composition Tree

```
App
├── GlobePlaceholder           (fixed inset-0, z-0, aria-hidden)
└── div (relative, z-10)
    ├── Navbar (z-30, sticky)
    │   └── GlassCard variant="navbar"
    │       ├── div "GHANA CAP" (gradient text)
    │       ├── TabNav
    │       │   └── button × 2-3 (filtered by userRole)
    │       └── div (right side)
    │           ├── ThemeToggle (lucide Moon/Sun)
    │           ├── div user-profile (skeleton | name+role | error)
    │           └── a href="/logout"
    └── main
        └── AnimatePresence mode="wait"
            └── motion.div key={tab}
                └── GlassCard (placeholder for Plans 03 + 04)
```

## Task Commits

Each task was committed atomically with proper conventional-commit form:

1. **Task 1: shared primitives** — `b48dea0` (`feat(04-02): add shared primitives — types, API client, socket, theme + useApi hooks`)
2. **Task 2: SPA shell** — `65a4ee4` (`feat(04-02): build SPA shell — Navbar + Tabs + ThemeToggle + GlassCard + GlobePlaceholder`)

(Plan-metadata commit will be added by the orchestrator finalization step.)

## Files Created / Modified

**Created (13 under `frontend/src/`):**

| File | Lines | Purpose |
|------|-------|---------|
| `lib/cn.ts` | 13 | clsx + tailwind-merge wrapper |
| `api/types.ts` | 113 | CapAlert / User / WorkflowStage / etc. |
| `api/client.ts` | 53 | `apiFetch<T>()` + `ApiError` |
| `api/socket.ts` | 27 | Typed Socket.IO singleton |
| `hooks/useTheme.ts` | 56 | Theme state + localStorage + data-theme sync |
| `hooks/useApi.ts` | 47 | Generic GET hook |
| `components/ui/GlassCard.tsx` | 36 | 3-variant glass wrapper |
| `components/ui/SeverityBadge.tsx` | 36 | Severity → color (substring-match) |
| `components/ui/StageBadge.tsx` | 33 | WorkflowStage → label + color |
| `components/layout/Navbar.tsx` | 70 | Brand + tabs + theme toggle + user + Logout |
| `components/layout/ThemeToggle.tsx` | 31 | Lucide Sun/Moon button |
| `components/layout/TabNav.tsx` | 56 | Tab buttons with role gate |
| `components/layout/GlobePlaceholder.tsx` | 25 | Static gradient + Phase 7 swap-point marker |

**Modified (1):**

- `frontend/src/App.tsx` — rewrote the 12-line Plan-01 placeholder into the 73-line shell that mounts `GlobePlaceholder + Navbar + AnimatePresence(motion.div(GlassCard))` and fetches `/api/v1/me` on mount.

## Final Exported Type Signatures (Plans 03 + 04 reference)

From `frontend/src/api/types.ts`:

```typescript
export type WorkflowStage = 0 | 1 | 3
export type Severity = 'Extreme' | 'Severe' | 'Moderate' | 'Minor' | 'Unknown'
export type Urgency  = 'Immediate' | 'Expected' | 'Future' | 'Past' | 'Unknown'
export type Certainty = 'Observed' | 'Likely' | 'Possible' | 'Unlikely' | 'Unknown'
export type Category = 'Met' | 'Geo' | 'Safety' | 'Security' | 'Rescue' | 'Fire'
                     | 'Health' | 'Env' | 'Transport' | 'Infra' | 'CBRNE' | 'Other'
export type CapStatus = 'Actual' | 'Exercise' | 'System' | 'Test' | 'Draft'
export type CapMsgType = 'Alert' | 'Update' | 'Cancel' | 'Ack' | 'Error'
export type CapScope = 'Public' | 'Restricted' | 'Private'
export type Role = 'Admin' | 'cap generator' | 'cap validator'

export interface CapAlert { /* 25 fields, mirrors process_alert_logic enriched_alert */ }
export interface User { staff_id; name; agency; role; email }
export interface AlertsListResponse { alerts: CapAlert[]; degraded: boolean; error? }
export interface ManualAlertRequest { /* form payload + optional CAP fields */ }
export interface ValidationRequest { action: 'approve' | 'reject'; reason? }
export interface DispatchSuccessResponse { status: 'success'; identifier; message }
export interface ApiErrorResponse { error: string }
export interface AgentDraftResponse { /* Plan 06 endpoint shape */ }
```

From `frontend/src/api/client.ts`:

```typescript
export class ApiError extends Error { status: number; payload: ApiErrorResponse | unknown }
export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T>
```

From `frontend/src/api/socket.ts`:

```typescript
export interface ServerToClientEvents {
  new_alert: (alert: CapAlert) => void
  alert_updated: (alert: CapAlert) => void
}
export const socket: Socket<ServerToClientEvents, ClientToServerEvents>
```

From `frontend/src/hooks/useTheme.ts`:

```typescript
export type Theme = 'light' | 'dark'
export function useTheme(): { theme: Theme; toggle: () => void; setTheme: (t: Theme) => void }
```

From `frontend/src/hooks/useApi.ts`:

```typescript
export interface UseApiState<T> { data: T | null; error: ApiError | null; loading: boolean; refetch: () => Promise<void> }
export function useApi<T>(path: string | null): UseApiState<T>
```

## Bundle-Size Delta (vs Plan 01 baseline)

| File | Plan 01 | Plan 02 | Delta (raw) | Delta (gzip) |
|------|---------|---------|-------------|--------------|
| `dist/index.html` | 1.28 kB | 1.28 kB | 0 | 0 |
| `dist/assets/index-*.css` | 7.43 kB | 17.50 kB | **+10.07 kB** | +1.82 kB |
| `dist/assets/index-*.js` | 194.93 kB | 359.30 kB | **+164.37 kB** | **+53.70 kB** |
| **modules transformed** | 29 | 2153 | +2124 | — |
| Cold build time | 887 ms | 3,250 ms | +2,363 ms | — |

The JS jump is dominated by `motion` (the `AnimatePresence` + `motion` exports pull in the full motion module graph), `lucide-react` (per-icon tree-shaking still loads the import-resolution shell), and `socket.io-client`. The CSS jump comes from Tailwind generating utility classes used by the new components. Both are within the band RESEARCH.md A4 anticipated for Phase 4 (no warning threshold tripped).

## Theme Port Verification

The Plan-01 `frontend/index.html` no-flash bootstrap script and the new `useTheme` hook agree on:

- localStorage key: `'theme'`
- localStorage values: `'light'` | `'dark'`
- Default when unset: `'dark'` (matches Jinja default at `ghana_cap_dashboard.html:543`)
- Attribute name: `data-theme`
- Attribute targets: BOTH `document.documentElement` (`<html>`) AND `document.body` (matches Plan 01's bootstrap which also sets both)

Manual smoke (deferred to Plan 05 manual-verify checkpoint, but spot-checked here): toggling the theme via the React button and refreshing the page preserves the chosen theme, because the bootstrap reads the same `localStorage.theme` value the hook just wrote.

## Decisions Made

- **`ApiError` uses explicit field declarations** rather than constructor parameter properties (`constructor(public status, ...)`). The toolchain's `tsconfig.app.json` sets `erasableSyntaxOnly: true` (TS 5.8+ default in `create-vite@6`), which forbids the shorthand because parameter properties require runtime emit (assignment to `this`). Two error lines, one trivial fix; the alternative (toggling off `erasableSyntaxOnly` project-wide) would erode a useful TS hardening guarantee for one file. Behaviorally identical.
- **`GlassCard` uses a fixed-key variant prop**, not class-variance-authority. PATTERNS.md confirmed exactly three glass flavors exist in the Jinja codebase (card / navbar / item); CVA's overhead pays off with ~5+ variants or compound conditions, neither of which applies. `class-variance-authority` is still in `package.json` for any later component (e.g., a Button with size+intent matrix); this plan didn't need it.
- **Tab is local `useState<TabId>`, not a router.** RESEARCH.md A6 / Open Question 2 explicitly defers a router. Phase 4 has no deep-link requirement; adding `react-router-dom` now creates rework when Plans 03 + 04 land.
- **Default theme is `'dark'`, not system-preference (`prefers-color-scheme`).** The plan's `key_reminders` mentioned system-preference fallback as an aspiration. The existing Jinja behavior at `ghana_cap_dashboard.html:543` is `localStorage.getItem('theme') || 'dark'` — pure default-dark with no media query. The Plan-01 no-flash bootstrap in `frontend/index.html:14` is identical. Adding system-preference fallback in `useTheme` would create a 1-frame contradiction with the bootstrap (bootstrap renders dark, hook discovers system=light, hook flips on first render → flash). Documented as Deviation #1 below.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocker fix] `ApiError` constructor-parameter properties banned by `erasableSyntaxOnly: true`**

- **Found during:** Task 1 (first `npm run build`).
- **Issue:** The plan's exact code for `client.ts` used `constructor(public status: number, public payload: ApiErrorResponse | unknown)`. The toolchain emitted:

  ```
  src/api/client.ts(8,15): error TS1294: This syntax is not allowed when 'erasableSyntaxOnly' is enabled.
  src/api/client.ts(8,38): error TS1294: This syntax is not allowed when 'erasableSyntaxOnly' is enabled.
  ```

  `erasableSyntaxOnly` is on by default in `tsconfig.app.json` from the `create-vite@6` scaffold (Plan 01) under TS 5.8+; parameter properties require runtime field-assignment emit and are therefore forbidden. The plan's code predates that default flip.
- **Fix:** Replaced with explicit field declarations (`status: number; payload: ApiErrorResponse | unknown`) and assigned in the constructor body. Two-line diff. Kept the existing `super(...)` call and `this.name = 'ApiError'` line.
- **Files modified:** `frontend/src/api/client.ts`.
- **Verification:** `npx tsc --noEmit` and `npm run build` both exit 0. The `ApiError` class still works identically — same constructor signature from the caller's perspective, same `.status` and `.payload` fields.
- **Committed in:** b48dea0 (Task 1 commit).

### Plan-Aspiration Carve-Outs (not deviations, documented for Plan 05's verifier)

**1. Default theme stays `'dark'`, not system-preference.** The plan key_reminders said `useTheme` should "default to system preference if no saved value". I kept the Jinja-port behavior (`localStorage.theme || 'dark'`) because:
- The Plan 01 no-flash bootstrap script in `frontend/index.html:14` already hard-codes `dark` as the default. Switching `useTheme` to `prefers-color-scheme` while leaving the bootstrap as-is would produce a 1-frame flash when a system-light user lands cold (bootstrap paints dark → hook reads system → React hydrates light).
- The existing Jinja behavior at `ghana_cap_dashboard.html:543` is the same dark-by-default, no-media-query pattern.
- Plan 05's manual-verify checkpoint can re-evaluate; if Plan 05 wants system-preference, the change is a 5-line diff in `useTheme.ts` AND `index.html` together, which deserves a coordinated commit.

This isn't a Rule-1/2/3 fix — it's a deliberate parity choice. Flagged here so reviewers don't think it was overlooked.

## Threat Flags

None. The plan's `<threat_model>` covered all surfaces this plan touches:

- T-04-10 (Tampering on user.name / user.role rendering): mitigated — React escapes text by default; no `dangerouslySetInnerHTML`.
- T-04-11 (Spoofing of `localStorage.theme`): accepted per plan — non-sensitive.
- T-04-12 (Privilege escalation via TabNav role gate bypass): mitigated — server still enforces at `manual_alert` route (`ghana_cap_app.py:228-243`); React gate is UX-only, exactly as documented.
- T-04-13 (Information disclosure of operator name + role in DOM): accepted per plan.
- T-04-14 (DoS from `useApi('/api/v1/me')` render loop): mitigated — `fetchOnce` is `useCallback`-memoized on a stable string `path`; no loop possible.
- T-04-15 (Tampering on Socket.IO singleton under StrictMode): mitigated — `io()` runs at module scope (`frontend/src/api/socket.ts`), not inside an effect; subscribers register in components with their own cleanup (Plan 03 pattern).

## Issues Encountered

**`erasableSyntaxOnly: true` rejects parameter properties.** ~30 seconds of build failure on Task 1 before pinning down the cause. Worth noting for Plans 03 + 04: any class with shorthand parameter properties needs the explicit-field rewrite. The plan code samples for those plans should be reviewed against this constraint when their RESEARCH.md sections are translated into PLAN.md.

## User Setup Required

None.

## Next Phase Readiness

- **Plan 04-03 (Pipeline tab):** ready. The shared primitives are in place (`apiFetch`, `socket`, `useApi`, `CapAlert`, `User`, `WorkflowStage`, `SeverityBadge`, `StageBadge`, `GlassCard`). Plan 03 will replace the `tab === 'pipeline'` branch in `App.tsx` with a real `<Pipeline />` component that calls `useApi<AlertsListResponse>('/api/v1/alerts')` + subscribes to `socket.on('new_alert' / 'alert_updated', ...)`.
- **Plan 04-04 (Manual Entry + Settings):** ready. Same primitives. The Navbar's `userRole`-driven hide rule for the Manual tab already works (verified via type-check; manual smoke deferred to Plan 05).
- **Plan 04-05 (cutover + checkpoint):** the shell is mountable; the manual-verify checkpoint will visually inspect the brand gradient, theme toggle persistence across refresh, tab transition animation, role gating, and the Logout link.

## Self-Check: PASSED

**Files verified to exist:**
- `frontend/src/lib/cn.ts` — FOUND
- `frontend/src/api/types.ts` — FOUND
- `frontend/src/api/client.ts` — FOUND
- `frontend/src/api/socket.ts` — FOUND
- `frontend/src/hooks/useTheme.ts` — FOUND
- `frontend/src/hooks/useApi.ts` — FOUND
- `frontend/src/components/ui/GlassCard.tsx` — FOUND
- `frontend/src/components/ui/SeverityBadge.tsx` — FOUND
- `frontend/src/components/ui/StageBadge.tsx` — FOUND
- `frontend/src/components/layout/Navbar.tsx` — FOUND
- `frontend/src/components/layout/ThemeToggle.tsx` — FOUND
- `frontend/src/components/layout/TabNav.tsx` — FOUND
- `frontend/src/components/layout/GlobePlaceholder.tsx` — FOUND
- `frontend/src/App.tsx` — FOUND (modified)
- `frontend/dist/index.html` — FOUND
- `frontend/dist/assets/index-Co7UY2iW.js` — FOUND
- `frontend/dist/assets/index-DFuImqXo.css` — FOUND

**Commits verified:**
- b48dea0 — FOUND (Task 1: shared primitives)
- 65a4ee4 — FOUND (Task 2: SPA shell)

**Verification commands:**
- `cd frontend && npx tsc --noEmit` — exits 0
- `cd frontend && npm run build` — exits 0; emits 359.30 kB JS / 17.50 kB CSS
- `pytest tests/ -q` — 37 passed (no Python touched)
- `grep -rn "from 'framer-motion'" frontend/src` — 0 matches (canonical `motion/react` only)
- `grep -n "react-router-dom" frontend/package.json` — 0 matches (no router added)

---
*Phase: 04-frontend-migration-to-react-vite-typescript-tailwind-framer-*
*Plan: 02*
*Completed: 2026-05-09*
