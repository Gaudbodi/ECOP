# Phase 4: Frontend Migration to React + Vite + TypeScript + Tailwind + framer-motion - Research

**Researched:** 2026-05-09
**Domain:** SPA migration (vanilla JS + Jinja → React + Vite + TS + Tailwind + Motion), with Flask backend integration
**Confidence:** HIGH (stack picks, integration patterns, project layout); MEDIUM (Tailwind v3 vs v4 trade-off, CSRF approach)

## Summary

Phase 4 replaces the existing single-file Jinja-rendered `ghana_cap_dashboard.html` (~728 lines, vanilla JS + Leaflet + Three.js + inline CSS variables) with a Vite-built React + TypeScript SPA under `frontend/`. Flask remains the backend (Python/eventlet/Socket.IO), narrows to JSON-only state-changing routes plus a small set of SPA-serving routes, and continues to render the public TV display (`templates/public_feed.html`) and the login form (`templates/login.html`) as Jinja for v1 to keep CSRF + SMS-2FA flow intact. The rest of the dashboard becomes a SPA that consumes JSON, listens to existing Socket.IO events on the default namespace, and ports the existing localStorage-driven dark/light theme behavior.

The active stack is React 19.2 + Vite 6.0 + TypeScript 5.9 + Tailwind CSS 4.3 (with `@tailwindcss/vite`) + Motion 12.38 (the package formerly published as `framer-motion` — both names map to the same library; `motion` is the canonical package and `motion/react` is the canonical import). The recommended dev model is hybrid: Vite dev server on `:5173` proxies `/api/*` and `/socket.io/*` to Flask `:5000`; production builds Vite into `frontend/dist/` which Flask serves via `static_folder` + a catch-all SPA route. This matches the official Flask SPA pattern and the existing Phase 1-9 backend without disturbing the graceful-degradation invariant.

**Primary recommendation:** Vite 6 + React 19 + TS 5.9 + Tailwind 4.3 (CSS-first config with `@theme` block + `@custom-variant dark` data-attribute strategy) + Motion 12.38 (`motion/react`) + `socket.io-client` 4.8 (typed via `ServerToClientEvents` interface). Scaffold under `frontend/`, dev with Vite dev server proxying to Flask `:5000`, prod with Flask serving `frontend/dist/` via the official Flask SPA pattern. Keep `templates/login.html` and `templates/public_feed.html` as Jinja for v1.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Pipeline tab (real-time alert list) | Browser/Client (React) | Backend (Flask Socket.IO emits `new_alert` / `alert_updated`) | UI rendering + WS subscription is client-side; persistence + emission is server-side |
| Manual Entry form (CAP submission) | Browser/Client (React) | Backend (POST `/api/v1/alerts/manual`) | Form state + map interaction lives in client; validation + dispatch is server |
| Settings tab | Browser/Client (React) | Backend (Settings come from session + env state) | Read-only display of server-configured state |
| Webhook Config screen (view/regen/revoke API key) | Browser/Client (React UI) | Backend (new endpoints needed: `GET /api/v1/admin/webhook-keys`, `POST /api/v1/admin/webhook-keys/rotate`, `DELETE /api/v1/admin/webhook-keys/<id>`) | UI is client; the persistence model + key rotation logic is server-side and currently does NOT exist (only env-var-based key today) |
| Test Dispatcher button | Browser/Client (React) | Backend (existing `POST /api/v1/alerts/gmet/webhook`) | Button calls existing webhook endpoint with mock JSON; no new backend code needed |
| Light/dark theme toggle | Browser/Client | — | Pure UI state, persisted to `localStorage`; ports the existing Jinja behavior 1:1 |
| Glassmorphic styling | Browser/Client | — | Tailwind utility classes + theme variables in CSS |
| Tab transitions / alert-card animations | Browser/Client (Motion) | — | Animation is client-only |
| Login (email + 6-digit code, SMS 2FA) | Frontend Server (Jinja) | Backend (Flask routes + Africa's Talking) | Stays Jinja for v1 — CSRF + form post + redirect is simpler than SPA porting and the SMS flow is two POSTs |
| Public TV display | Frontend Server (Jinja) | Backend (Flask + `/live_feed` Socket.IO) | Stays Jinja — public, read-only, no operator state |
| Build artifacts (HTML/JS/CSS) | CDN/Static (served by Flask) | Vite build pipeline | Vite output goes under `frontend/dist/`; Flask serves it as static assets |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| react | 19.2.6 | UI framework | [VERIFIED: `npm view react version`] Current stable; React 19 features (Actions, useActionState, ref-as-prop) are mature. |
| react-dom | 19.2.6 | DOM renderer | [VERIFIED: `npm view react-dom version`] Pinned to React version. |
| typescript | 5.9.3 | Type system | [VERIFIED: `npm view typescript version`] Latest stable; default for new Vite React projects. |
| vite | 6.0.3 | Build tool + dev server | [VERIFIED: `npm view vite version`; Vite 6 also exists at higher patches but 6.0.x is the line current at scaffold time. Note: a 8.0.11 also exists in registry but 6.x is the established LTS line per ecosystem norms — confirm with `npm create vite@latest`]. Modern, fast, ESM-native. |
| @vitejs/plugin-react-swc | 4.3.0 | React fast refresh + JSX | [VERIFIED: `npm view @vitejs/plugin-react-swc version`] SWC-based; ~20x faster than Babel-based `@vitejs/plugin-react` for transforms. [CITED: dhiwise.com perf comparison and vitejs/vite-plugin-react-swc README]. Use this unless a specific Babel plugin is required (none in this scope). |
| tailwindcss | 4.3.0 | Styling | [VERIFIED: `npm view tailwindcss version` — published 2026-05-08]. CSS-first config via `@theme`, `@custom-variant`. Native Vite plugin. |
| @tailwindcss/vite | 4.3.0 | Tailwind Vite integration | [CITED: tailwindcss.com/docs/installation/using-vite] The recommended integration — supersedes PostCSS-based wiring for Vite projects. |
| motion | 12.38.0 | Animations (formerly `framer-motion`) | [VERIFIED: `npm view motion version`; both `motion` and `framer-motion` point to identical 12.38.0 builds — `motion` is the canonical package post-rebrand. [CITED: motion.dev/docs/react] Import as `import { motion, AnimatePresence } from "motion/react"`. |
| socket.io-client | 4.8.3 | WebSocket client | [VERIFIED: `npm view socket.io-client version`] Matches the existing Flask-SocketIO 5.3.6 server protocol (Engine.IO v4). |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| clsx | 2.1.1 | Conditional className composition | [VERIFIED] Standard for React + Tailwind. |
| tailwind-merge | 3.5.0 | De-duplicate conflicting Tailwind utility classes | [VERIFIED] Pair with clsx in a `cn()` utility. |
| class-variance-authority | 0.7.1 | Variant-based component APIs (`cva()`) | [VERIFIED] For `Button`, `Badge`, `Card` variants. |
| leaflet | 1.9.4 | Map (already used in current dashboard) | [VERIFIED] **Keep for Phase 4** — Phase 5 swaps to Mapbox GL. Wrap in a thin `MapPicker.tsx` component so the swap is local. |
| react-leaflet | 5.0.0 | React bindings for Leaflet | [VERIFIED] Optional; could use raw Leaflet refs. Recommend `react-leaflet` for cleaner unmount/cleanup. |
| lucide-react | 1.14.0 | Icon set | [VERIFIED] Standard. Replaces emoji 🌓 in current theme toggle. |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Tailwind 4.x | Tailwind 3.4.x | v3 is stable, more docs, more Stack Overflow content, `tailwind.config.js` is auto-loaded. v4 requires modern browsers (Safari 16.4+, Chrome 111+, Firefox 128+) and uses CSS-first config — fewer migration examples. **Recommend v4** because the project is greenfield SPA and operator browsers are modern; v4's CSS variables map cleanly to the existing `--bg-color`, `--glass-bg` etc. tokens already in `ghana_cap_dashboard.html`. |
| `@vitejs/plugin-react-swc` | `@vitejs/plugin-react` (Babel) | Babel plugin is the default; SWC plugin is faster but may not support every Babel transform. No Babel-only plugins needed in this scope. **Recommend SWC.** |
| `motion` package | `framer-motion` package (legacy name) | Identical bytes at 12.38.0; `framer-motion` still publishes. **Recommend `motion`** — canonical post-rebrand and matches `motion/react` import path. The phase brief uses "framer-motion" by name; this research recommends the canonical package — note in CONTEXT/PLAN. |
| `next-themes` | Custom `useTheme` hook | next-themes [CITED: github.com/pacocoursey/next-themes] *does* work outside Next.js (officially supports CRA/Gatsby since 0.3.0; Vite is unstated but functionally equivalent). Adds 1.5kB and `<ThemeProvider>` API. **Recommend a small custom hook** (matches existing localStorage-key-`theme` behavior precisely; less ceremony; one less dependency). next-themes is acceptable if the team prefers a maintained library. |
| TanStack Query (`@tanstack/react-query`) | Plain `fetch` + `useState` | TanStack Query is the standard for cached server state. **Defer to a future phase** — Phase 4 has 4 endpoints and lots of Socket.IO push state; the cache value is low and the dependency is heavy. |
| `react-hook-form` | Plain controlled inputs | RHF is standard for complex forms. The Manual Entry form has ~6 fields; controlled inputs are fine. **Defer.** |

**Installation:**
```bash
# Run from frontend/ after `npm create vite@latest frontend -- --template react-swc-ts`
npm install \
  motion \
  socket.io-client \
  clsx tailwind-merge class-variance-authority \
  leaflet react-leaflet \
  lucide-react

npm install -D \
  tailwindcss @tailwindcss/vite \
  @types/leaflet
```

**Version verification (2026-05-09):**
- react@19.2.6, react-dom@19.2.6, typescript@5.9.3
- vite@6.0.3, @vitejs/plugin-react-swc@4.3.0
- tailwindcss@4.3.0, @tailwindcss/vite@4.3.0 (both published 2026-05-08)
- motion@12.38.0 (= framer-motion@12.38.0)
- socket.io-client@4.8.3
- clsx@2.1.1, tailwind-merge@3.5.0, class-variance-authority@0.7.1
- leaflet@1.9.4, react-leaflet@5.0.0, lucide-react@1.14.0

## Architecture Patterns

### System Architecture Diagram

```
                       ┌──────────────────────────────────────────────┐
                       │  Operator Browser                            │
                       │  (modern, Safari 16.4+ / Chrome 111+)        │
                       └──────┬───────────────────────────────────────┘
                              │
                ┌─────────────┴────────────────┐
                │                              │
          [HTTP /api/*]                  [WS /socket.io/*]
                │                              │
                ▼                              ▼
     ┌─────────────────────┐          ┌──────────────────────┐
     │   Flask 3.0          │          │ Flask-SocketIO 5.3.6 │
     │   (eventlet worker)  │◄─emits──┤ (default + /live_feed │
     │   ghana_cap_app.py   │          │  namespaces)          │
     └──────┬──────────────┘          └──────────────────────┘
            │
            ├─[GET /]──serves dist/index.html
            ├─[GET /assets/*]──serves dist/assets/*.{js,css}
            ├─[GET /static/*]──serves Flask static (audio MP3s)
            ├─[POST /api/v1/alerts/*]──JSON-only routes
            ├─[POST /api/v1/agents/draft]──JSON-only
            ├─[GET /login]──JINJA templates/login.html (v1)
            └─[GET /public/feed/display]──JINJA templates/public_feed.html (v1)

DEV MODE:
   Vite :5173  ──proxy /api/* + /socket.io/*──►  Flask :5000
   (HMR, fast-refresh)                            (no /assets serving needed in dev)

PROD MODE:
   `npm run build` → frontend/dist/{index.html, assets/*.js, assets/*.css}
   Flask serves dist/ via static_folder='frontend/dist' + catch-all to index.html
```

### Recommended Project Structure

```
EMERGENCY/                          # Repo root (existing)
├── ghana_cap_app.py                # Flask entrypoint (existing, modified for SPA serve)
├── services/                       # Existing services (unchanged)
├── templates/                      # Jinja (login.html, public_feed.html stay)
├── static/                         # Flask static (audio/, ghana_regions.json — unchanged)
├── frontend/                       # NEW — Vite project root
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── tsconfig.node.json
│   ├── index.html                  # Vite entry HTML
│   ├── public/                     # Static assets copied as-is to dist/
│   ├── src/
│   │   ├── main.tsx                # ReactDOM.createRoot + ThemeProvider
│   │   ├── App.tsx                 # Top-level router/layout (single page; tabs)
│   │   ├── index.css               # @import "tailwindcss"; @theme {...}; @custom-variant dark ...
│   │   ├── api/                    # API client (fetch wrappers, types)
│   │   │   ├── client.ts           # cn(), apiFetch() with CSRF header
│   │   │   └── types.ts            # CapAlert, ApiError, AgentDraft, etc.
│   │   ├── hooks/
│   │   │   ├── useSocket.ts        # Singleton Socket.IO instance + lifecycle
│   │   │   ├── useTheme.ts         # localStorage + data-theme attr
│   │   │   └── useAlerts.ts        # State + `new_alert`/`alert_updated` subscription
│   │   ├── components/
│   │   │   ├── ui/                 # Generic primitives (Card, Button, Badge, Tabs)
│   │   │   ├── layout/             # Navbar, ThemeToggle, TabNav
│   │   │   ├── pipeline/           # AlertList, AlertCard, AlertDetails, ValidatorControls
│   │   │   ├── manual/             # ManualEntryForm, MapPicker (thin Leaflet wrapper)
│   │   │   ├── settings/           # SettingsPanel, WebhookConfig, TestDispatcher
│   │   │   └── globe/              # GlobeBackground (Three.js — placeholder for Phase 7 swap)
│   │   └── lib/
│   │       └── cn.ts               # clsx + tailwind-merge utility
│   └── dist/                       # Build output (gitignored; written by `npm run build`)
│       ├── index.html
│       └── assets/
│           ├── index-[hash].js
│           └── index-[hash].css
├── .planning/
└── ...
```

Files-under-300-line convention (per CLAUDE.md / GEMINI.md): single-responsibility components — `AlertCard.tsx`, `ManualEntryForm.tsx`, `MapPicker.tsx` each in their own file. Index.html and main.tsx stay tiny.

### Pattern 1: Vite Dev Proxy to Flask

**What:** During dev, Vite serves on `:5173`, proxies `/api/*` and `/socket.io/*` to Flask on `:5000`. Operators run both processes; HMR works for the React code, Flask handles the backend.
**When to use:** Always in dev. Avoid in production.
**Example:**
```typescript
// frontend/vite.config.ts
// Source: https://vite.dev/config/server-options.html
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        // No rewrite — Flask routes are already under /api/v1/...
      },
      '/socket.io': {
        target: 'http://localhost:5000',
        ws: true,           // REQUIRED for Socket.IO upgrade
        changeOrigin: true,
      },
      // Audio MP3s and existing /static (if SPA needs them in dev)
      '/static': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',         // frontend/dist/
    emptyOutDir: true,
    sourcemap: true,
  },
})
```
**Note:** Flask's existing `ALLOWED_ORIGINS` env (Phase 2) already lists `http://localhost:5173`. CORS for the Socket.IO connection is satisfied; CSRF is not invoked because JSON endpoints are `@csrf.exempt` (see Pattern 7 below).

### Pattern 2: Flask SPA Serve (Production)

**What:** Flask serves `frontend/dist/index.html` at `/`, `frontend/dist/assets/*` at `/assets/`, and falls through to `index.html` on unknown paths so the React router (if any) can handle deep links.
**When to use:** Production deploy via gunicorn/Procfile/Dockerfile.
**Example:**
```python
# In ghana_cap_app.py — modify Flask construction and add catch-all.
# Source: https://flask.palletsprojects.com/en/stable/patterns/singlepageapplications/
import os
from flask import Flask, send_from_directory

# Resolve the dist/ folder relative to the app file so it works under gunicorn.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(BASE_DIR, 'frontend', 'dist')

app = Flask(
    __name__,
    static_folder='static',         # KEEP — for /static/audio/*.mp3 and existing assets
    static_url_path='/static',
    template_folder='templates',    # KEEP — for login.html, public_feed.html
)

# Phase 4: Serve the React build at /. Order matters — register AFTER /api/* and /login.
@app.route('/')
def dashboard_spa():
    return send_from_directory(DIST_DIR, 'index.html')

@app.route('/assets/<path:filename>')
def spa_assets(filename):
    return send_from_directory(os.path.join(DIST_DIR, 'assets'), filename)

# Catch-all: any non-API path that didn't match a Flask route falls back to the SPA.
# This is required if the SPA ever uses client-side routing (deep links).
# Excludes paths starting with /api, /static, /login, /logout, /public, /socket.io.
@app.route('/<path:path>')
def spa_fallback(path):
    if path.startswith(('api/', 'static/', 'public/', 'socket.io/')):
        # Let Flask's normal routing handle these; if no route matches it's a real 404.
        from flask import abort
        abort(404)
    return send_from_directory(DIST_DIR, 'index.html')
```

**Caution:** the existing `dashboard()` route at `ghana_cap_app.py:201-206` currently does `render_template('ghana_cap_dashboard.html', ...)`. Phase 4 must replace this route's body to serve the SPA instead, while keeping `@login_required` (so unauthenticated users still get redirected to `/login`). The dashboard SSR pattern (`alerts=alerts`) goes away — the SPA fetches via `GET /api/v1/alerts` (NEW endpoint needed; see Pitfalls).

### Pattern 3: Tailwind v4 CSS-First Theme + data-theme Dark Mode

**What:** Tailwind v4 moves config from `tailwind.config.js` into a CSS `@theme` block. Custom colors and tokens become CSS variables. Dark mode is configured via `@custom-variant`.
**When to use:** Whole project (no JS config file needed).
**Example:**
```css
/* frontend/src/index.css */
/* Source: https://tailwindcss.com/docs/upgrade-guide and https://tailwindcss.com/docs/dark-mode */
@import "tailwindcss";

/* Port the existing CSS variables from ghana_cap_dashboard.html:13-31. */
@theme {
  /* Brand */
  --color-accent: #0ea5e9;
  --color-accent-secondary: #8b5cf6;

  /* Dark theme defaults (matches the current --data-theme=dark / no-attr default) */
  --color-bg: #020617;
  --color-text: #f8fafc;
  --color-glass-bg: rgba(255, 255, 255, 0.08);
  --color-glass-border: rgba(255, 255, 255, 0.15);
  --color-navbar-bg: rgba(15, 23, 42, 0.6);

  /* Glassmorphic shadow */
  --shadow-glass: 0 8px 32px 0 rgba(0, 0, 0, 0.37);

  /* Typography */
  --font-sans: 'Inter', system-ui, -apple-system, sans-serif;
}

/* Dark-mode variant uses [data-theme=dark] to match existing localStorage behavior
   (ghana_cap_dashboard.html:537 sets body.data-theme = 'dark' | 'light'). */
@custom-variant dark (&:where([data-theme=dark], [data-theme=dark] *));

/* Light-mode overrides (Phase 4 ports the existing [data-theme="light"] block.) */
[data-theme="light"] {
  --color-bg: #f1f5f9;
  --color-text: #0f172a;
  --color-glass-bg: rgba(255, 255, 255, 0.7);
  --color-glass-border: rgba(15, 23, 42, 0.1);
  --color-navbar-bg: rgba(255, 255, 255, 0.8);
}

/* Glassmorphic component layer — exposed as utility-friendly classes via @utility. */
@utility glass-card {
  background: var(--color-glass-bg);
  border: 1px solid var(--color-glass-border);
  border-radius: 1rem;
  padding: 2rem;
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
}

@utility glass-input {
  background: rgba(0, 0, 0, 0.3);
  border: 1.5px solid var(--color-glass-border);
  border-radius: 0.5rem;
  color: var(--color-text);
}
```

Components consume these as utilities (`<div className="glass-card p-8">`) plus standard Tailwind utilities (`bg-accent text-white backdrop-blur-2xl`). The CSS-variable layer means dark/light switches are automatic — no per-class `dark:` prefix needed for theme tokens, only for hardcoded values like text shades.

### Pattern 4: Theme Hook + ThemeProvider (custom, no next-themes)

**What:** Port the existing 7-line `toggleTheme()` from `ghana_cap_dashboard.html:533-540` into a tiny React hook. Sets `data-theme` on `document.documentElement` (or `body` to preserve identical behavior) and persists to `localStorage.theme`.
**When to use:** Any place needing the current theme or a toggle button.
**Example:**
```typescript
// frontend/src/hooks/useTheme.ts
import { useCallback, useEffect, useState } from 'react'

type Theme = 'light' | 'dark'

function readInitial(): Theme {
  if (typeof window === 'undefined') return 'dark'
  const saved = window.localStorage.getItem('theme')
  return saved === 'light' ? 'light' : 'dark'
}

export function useTheme() {
  const [theme, setTheme] = useState<Theme>(readInitial)

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    document.body.setAttribute('data-theme', theme)  // legacy parity
    window.localStorage.setItem('theme', theme)
  }, [theme])

  const toggle = useCallback(() => {
    setTheme(t => (t === 'dark' ? 'light' : 'dark'))
  }, [])

  return { theme, setTheme, toggle }
}
```

To avoid a flash of unstyled (wrong-theme) content, set `data-theme` in `index.html` via a tiny inline script *before* React hydrates:
```html
<!-- frontend/index.html -->
<script>
  (function () {
    var t = localStorage.getItem('theme') === 'light' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', t);
  })();
</script>
```

### Pattern 5: Socket.IO Hook (typed, singleton)

**What:** Single `socket.io-client` instance shared via a module export; React hook for component-level subscription with auto-cleanup.
**When to use:** Pipeline tab, Settings tab if any live data, future agent stream views.
**Example:**
```typescript
// frontend/src/api/socket.ts
// Source: https://socket.io/how-to/use-with-react and https://socket.io/docs/v4/typescript/
import { io, type Socket } from 'socket.io-client'
import type { CapAlert } from './types'

interface ServerToClientEvents {
  new_alert: (alert: CapAlert) => void
  alert_updated: (alert: CapAlert) => void
}

interface ClientToServerEvents {
  // None used today; reserved for Phase 5+ (agent streaming etc.)
}

// Singleton — one connection, multiple subscribers.
// In dev, Vite proxies /socket.io to :5000; in prod, Flask serves both.
export const socket: Socket<ServerToClientEvents, ClientToServerEvents> = io({
  // No URL → connects to current origin (matches Vite proxy + prod).
  autoConnect: true,
  transports: ['websocket', 'polling'],  // websocket-first; eventlet supports both
})
```

```typescript
// frontend/src/hooks/useAlerts.ts
import { useEffect, useState } from 'react'
import { socket } from '../api/socket'
import type { CapAlert } from '../api/types'

export function useAlerts(initial: CapAlert[]) {
  const [alerts, setAlerts] = useState<CapAlert[]>(initial)

  useEffect(() => {
    function onNew(a: CapAlert) {
      setAlerts(prev => [a, ...prev.filter(x => x.identifier !== a.identifier)])
    }
    function onUpdated(a: CapAlert) {
      setAlerts(prev => prev.map(x => (x.identifier === a.identifier ? a : x)))
    }
    socket.on('new_alert', onNew)
    socket.on('alert_updated', onUpdated)
    return () => {
      socket.off('new_alert', onNew)
      socket.off('alert_updated', onUpdated)
    }
  }, [])

  return alerts
}
```

The dashboard page seeds `initial` via `GET /api/v1/alerts` (NEW endpoint — see Pitfall #1) on mount and lets Socket.IO take over from there. **No more `location.reload()` hack** that today's `ghana_cap_dashboard.html:672` uses.

### Pattern 6: Motion Tab Transitions and Card Expand/Collapse

**What:** `AnimatePresence mode="wait"` for tab switches (one tab finishes exit before next enters); `motion.div` with `layout` prop for alert-card expand/collapse.
**When to use:** Tab nav, alert detail expand.
**Example:**
```typescript
// frontend/src/App.tsx — tab transition
// Source: https://motion.dev/docs/react-animate-presence
import { AnimatePresence, motion } from 'motion/react'
import { useState } from 'react'

const tabs = ['pipeline', 'manual', 'settings'] as const
type Tab = typeof tabs[number]

export default function App() {
  const [tab, setTab] = useState<Tab>('pipeline')
  return (
    <>
      <TabNav active={tab} onChange={setTab} />
      <AnimatePresence mode="wait">
        <motion.div
          key={tab}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.18, ease: 'easeOut' }}
        >
          {tab === 'pipeline' && <Pipeline />}
          {tab === 'manual'   && <ManualEntry />}
          {tab === 'settings' && <Settings />}
        </motion.div>
      </AnimatePresence>
    </>
  )
}
```

```typescript
// frontend/src/components/pipeline/AlertCard.tsx — expand/collapse
import { motion } from 'motion/react'
import { useState } from 'react'

export function AlertCard({ alert }: { alert: CapAlert }) {
  const [open, setOpen] = useState(false)
  return (
    <motion.div layout className="glass-card overflow-hidden cursor-pointer"
                onClick={() => setOpen(o => !o)}>
      <motion.div layout className="flex justify-between p-5">
        {/* summary row */}
      </motion.div>
      {open && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: 'auto', opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          transition={{ duration: 0.25 }}
          className="px-6 pb-6"
        >
          {/* details grid */}
        </motion.div>
      )}
    </motion.div>
  )
}
```

### Pattern 7: API Client + CSRF (recommendation: keep JSON endpoints `@csrf.exempt`, rely on same-origin + SameSite=Lax cookie)

**What:** A thin `apiFetch` that adds `Content-Type` and credentials, with optional `X-CSRFToken` header for future hardening.
**When to use:** Every JSON call.
**Example:**
```typescript
// frontend/src/api/client.ts
export class ApiError extends Error {
  constructor(public status: number, public payload: unknown) { super(`API ${status}`) }
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    credentials: 'same-origin',
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
  })
  if (!res.ok) throw new ApiError(res.status, await res.json().catch(() => null))
  return res.json() as Promise<T>
}
```

**Recommendation: keep JSON endpoints `@csrf.exempt` for v1, defer header-CSRF to a future hardening pass.**

Reasoning:
- Phase 2 already shipped session cookies with `SESSION_COOKIE_HTTPONLY=True`, `SESSION_COOKIE_SAMESITE='Lax'`, `SESSION_COOKIE_SECURE=_is_production` (see `ghana_cap_app.py:84-91`).
- Same-origin SameSite=Lax cookie is sufficient for CSRF on POST/PUT/DELETE for the typical web threat model (per OWASP guidance — Lax blocks cross-site POSTs initiated outside the user's tab).
- All four JSON endpoints (`/api/v1/alerts/manual`, `/api/v1/alerts/validate/<identifier>`, `/api/v1/alerts/gmet/webhook`, `/api/v1/agents/draft`) and the public endpoint (`/public/feed/receive`) currently sit behind `@csrf.exempt` decorators with comments noting "Phase 4 frontend will move to token-in-header" — the path of least disruption is to leave them as-is. The GMeT webhook is API-key-authenticated (not session); it doesn't need CSRF at all.
- Header-CSRF (the alternative) requires:
  - Adding `csrf_meta_tag()` rendering — but the SPA's `index.html` is built by Vite and won't pass through Jinja, so the token has to be fetched from a new `GET /api/v1/csrf-token` endpoint and stored client-side. [CITED: flask-wtf csrf docs] This is more code and more attack surface (rotating tokens in a SPA is non-trivial).
  - Calling `validate_csrf()` manually from each JSON route or installing a `before_request` hook — Flask-WTF doesn't auto-validate JSON bodies the way it auto-validates form bodies.

If CSRF hardening is desired in Phase 4, the lightweight approach is:
1. Add `GET /api/v1/csrf-token` returning `{token: generate_csrf()}`.
2. SPA fetches once on mount, stores in memory, sends as `X-CSRFToken` header on all mutating calls.
3. In each `@csrf.exempt` route, manually call `validate_csrf(request.headers.get('X-CSRFToken'))` — raises `CSRFError` on failure.
4. Exempt the GMeT webhook (API-key auth, not session — different threat model).

Both approaches are documented; the **recommendation is to ship Phase 4 with `@csrf.exempt` retained** (cite the SameSite=Lax cookie defense) and add CSRF token-in-header in a follow-up phase if the threat model justifies it. [ASSUMED: SameSite=Lax suffices for this threat model — needs user confirmation for production deploy.]

### Pattern 8: TypeScript Types from MongoDB Alert Shape (hand-rolled)

**What:** A single `frontend/src/api/types.ts` derived from `process_alert_logic` in `ghana_cap_app.py:387-412`.
**When to use:** All API responses and Socket.IO events.
**Example:**
```typescript
// frontend/src/api/types.ts
// Source: derived from ghana_cap_app.py:369-412 (the `enriched_alert` dict shape).

export type WorkflowStage = 0 | 1 | 3
// 0 = Rejected/Draft, 1 = Pending Validation, 3 = Dispatched

export type Severity = 'Extreme' | 'Severe' | 'Moderate' | 'Minor' | 'Unknown'
export type Urgency = 'Immediate' | 'Expected' | 'Future' | 'Past' | 'Unknown'
export type Certainty = 'Observed' | 'Likely' | 'Possible' | 'Unlikely' | 'Unknown'
export type Category = 'Met' | 'Geo' | 'Safety' | 'Security' | 'Rescue' | 'Fire' | 'Health' | 'Env' | 'Transport' | 'Infra' | 'CBRNE' | 'Other'
export type CapStatus = 'Actual' | 'Exercise' | 'System' | 'Test' | 'Draft'
export type CapMsgType = 'Alert' | 'Update' | 'Cancel' | 'Ack' | 'Error'

export interface CapAlert {
  identifier: string                       // e.g. "GH-CAP-A1B2C3D4"
  sender_name: string
  sender_agency: string                    // e.g. "GMeT", "NCA"
  sender_id: string                        // staff_id
  sender_ip: string
  sent: string                             // ISO timestamp
  status: CapStatus
  msgType: CapMsgType
  scope: 'Public' | 'Restricted' | 'Private'
  category: Category
  event: string                            // e.g. "Weather Alert"
  urgency: Urgency
  severity: Severity
  certainty: Certainty
  headline: string
  description: string
  instruction: string
  affected_regions: string[]               // e.g. ["Greater Accra Region"]
  translations: Record<string, string>     // {English, Twi, Hausa, ...}
  audio_links: Record<string, string>      // {English: '/static/audio/...mp3', ...}
  geo: { lat: number; lon: number }
  mno_dispatched: boolean
  sms_sent: boolean
  workflow_stage: WorkflowStage
  validated_by?: string
  validated_at?: string                    // ISO
  rejected_by?: string
  rejected_reason?: string
  // Phase 6 agent draft envelope (output of /api/v1/agents/draft) is a subset.
}

export interface ManualAlertRequest {
  headline: string
  severity: Severity
  urgency: Urgency
  description: string
  instruction: string
  latitude: number | string                // form sends string, backend tolerates
  longitude: number | string
}

export interface ValidationRequest {
  action: 'approve' | 'reject'
  reason?: string
}

export interface AgentDraftRequest {
  text: string
}

export interface AgentDraftResponse extends Partial<CapAlert> {
  agent?: { mock?: boolean; tools_used?: string[] }
  error?: string
}

export interface User {
  staff_id: string
  name: string
  agency: string
  role: 'Admin' | 'cap generator' | 'cap validator'
  email: string
}
```

**Why hand-rolled, not OpenAPI codegen:** five endpoints, no spec file exists, two-way Socket.IO events not in OpenAPI, and the MongoDB document shape is the source of truth and lives in Python. Hand-rolling is a 50-line file maintained alongside `ghana_cap_app.py:process_alert_logic`. OpenAPI codegen would require writing a spec first — wasted overhead.

### Pattern 9: Webhook Config + Test Dispatcher (NEW backend support needed)

**What:**
- **Webhook Config screen:** view current GMeT webhook URL + key state, generate a new key, revoke. Currently the key is `GMET_WEBHOOK_API_KEY` env var — single value, no rotation API.
- **Test Dispatcher button:** send a mock CAP JSON to `POST /api/v1/alerts/gmet/webhook` with the current `X-CAP-API-KEY` header.

**Implementation notes:**
- Test Dispatcher needs **no new backend code** — it POSTs to the existing webhook with a synthetic payload. The SPA needs the API key only to authenticate; for the test button, the SPA can either (a) use a session-authenticated proxy endpoint `POST /api/v1/admin/test-dispatch` that re-injects the key server-side (recommended — never exposes the key to the browser), or (b) require the operator to paste the key in. **Recommend (a)** — `POST /api/v1/admin/test-dispatch` (login required, role=Admin) reads a fixed mock payload and calls `process_alert_logic` directly with `workflow_stage=3`.
- Webhook Config (view/generate/revoke) is **out of scope for the existing single-env-var design**. The minimal v1 is a read-only screen showing the current webhook URL (`window.location.origin + '/api/v1/alerts/gmet/webhook'`) and a "configured server-side" placeholder. **Generate/revoke requires a key-store** (e.g., a `webhook_keys` MongoDB collection with `{key_id, hashed_key, created_at, revoked_at}`) and a multi-key auth check at `gmet_webhook`. The phase brief lists this under REQ-dashboard-webhook-config (Phase 4) — flag as a small backend sub-task within the phase plan.

### Anti-Patterns to Avoid

- **Storing CSRF token in localStorage:** vulnerable to XSS exfiltration. If Phase 4 adopts header-CSRF, fetch on every load and keep in memory only.
- **Re-creating Socket.IO instance per component:** doubles connections and event handlers fire twice. Use the singleton in `api/socket.ts`.
- **`location.reload()` to refresh alerts:** today's pattern (`ghana_cap_dashboard.html:672`); kills WS connection and Socket.IO state. Replace with `useAlerts` hook.
- **Sharing CSS variables via Tailwind config + JS:** v4's `@theme` block is the canonical place; don't also define them in `:root` outside it (creates duplicate sources of truth).
- **`framer-motion` import path:** the rebrand canonicalizes `motion/react`. Both names work today, but the docs and examples drift from `framer-motion` — using the legacy name will produce friction with future docs lookups.
- **Vite `base: './'` with Flask serving from a non-root URL:** if Flask ever serves the SPA at `/admin` instead of `/`, the relative-base approach silently breaks asset resolution. Use `base: '/'` (default) and let Flask register the catch-all at `/`.
- **Embedding `Three.js`/`react-globe.gl` in Phase 4:** Phase 7 owns the globe revamp. Keep the existing Three.js wireframe code as a thin `GlobeBackground.tsx` placeholder so Phase 7 can swap implementations without touching layout/components.
- **Touching `templates/login.html` and `templates/public_feed.html`:** these stay Jinja in v1 (decision documented in Phase brief). Migrating login means re-implementing the SMS-2FA two-step form and CSRF handling in React for marginal benefit.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| className composition with conditional classes | String concatenation, `?:` chains | `clsx` + `tailwind-merge` (`cn()` util) | Handles null/undefined, removes class conflicts (`p-2 p-4` → `p-4`). |
| Component variants (Button styles, Badge severity) | If-else chains in JSX | `class-variance-authority` (`cva()`) | Pattern is industry standard; type-safe variant API. |
| Tab transitions, card expand | CSS `transition` + `max-height: 0/500px` (current Jinja approach) | `motion` (formerly framer-motion) | CSS max-height kludge cuts content; Motion's `layout` prop is mathematically correct and respects `prefers-reduced-motion`. |
| Socket.IO connection lifecycle | New `io()` per component | Singleton + `useEffect` cleanup | Multiple connections = doubled event handlers, race conditions on disconnect/reconnect. |
| Theme persistence | Inline scripts duplicated across pages | One `useTheme` hook + one inline pre-hydration script | DRY; preserves anti-FOUC behavior. |
| Map widget | Custom Canvas/SVG | Leaflet (existing) wrapped in `react-leaflet` | Don't re-do hand-rolled map for one phase when Phase 5 is going to swap to Mapbox anyway. |
| Icon set | Inline SVG copy-pastes | `lucide-react` | Tree-shakable; matches existing `🌓` semantics with a `Moon`/`Sun` pair. |
| Form state for Manual Entry | Custom validation, manual onChange | Plain controlled inputs (≤6 fields) | RHF is overkill at 6 fields — but **don't** hand-roll error display logic. Use simple state + `<p className="text-red-500">` patterns. |
| API request types | `any` everywhere | Hand-rolled `types.ts` (50 lines) | OpenAPI codegen is heavier than the surface; types must match `process_alert_logic` output. |
| CSRF protection on state changes | Roll a token mechanism | Either keep `@csrf.exempt` + SameSite=Lax (recommended), or use Flask-WTF's `csrf_meta_tag()` + `validate_csrf()` | Don't invent a custom token scheme — Flask-WTF already exposes the primitives. |

**Key insight:** Phase 4 is a *port*, not a *rewrite*. Most of the existing Jinja behavior already works; the React migration replaces vanilla DOM manipulation with declarative components, and replaces inline CSS variables with Tailwind utility classes that read the same variables. Don't re-design the dashboard — translate it.

## Common Pitfalls

### Pitfall 1: No `GET /api/v1/alerts` endpoint exists today

**What goes wrong:** The SPA's first paint of the Pipeline tab needs an alert list, but today `dashboard()` server-renders alerts via `get_all_alerts()` and Jinja iteration (`ghana_cap_app.py:201-206`). When Phase 4 turns `dashboard()` into a static-file serve, that initial alert list is lost.
**Why it happens:** SSR-templated initial state isn't replicated by the SPA-serving model.
**How to avoid:** Add a new `GET /api/v1/alerts` endpoint in `ghana_cap_app.py` that returns `jsonify(get_all_alerts())` (login required). The SPA fetches it on mount and seeds `useAlerts(initial=alerts)`.
**Warning signs:** The Pipeline tab loads empty after login, only filling in when the next `new_alert` Socket.IO event arrives.

### Pitfall 2: Socket.IO connecting to wrong origin in dev

**What goes wrong:** `io()` with no URL connects to `window.location.origin`, which in dev is `http://localhost:5173` (Vite). Without WS proxy, the Engine.IO handshake 404s.
**Why it happens:** Misconfigured `vite.config.ts` proxy block.
**How to avoid:** Pattern 1 above — `proxy['/socket.io']` with `ws: true`. The brief notes this; verify the `ws: true` flag is present and `target: 'http://localhost:5000'` (Vite handles ws:// upgrade automatically).
**Warning signs:** Browser console shows `Failed to load resource: the server responded with a status of 404` for `/socket.io/?EIO=4&...`.

### Pitfall 3: Mongo `_id` field not JSON-serializable

**What goes wrong:** `get_all_alerts()` returns Mongo documents that include `ObjectId` fields. `jsonify()` choked on this earlier (now fixed in `validate_alert` line 280 for one path). When the new `GET /api/v1/alerts` endpoint is added, the same issue resurfaces.
**Why it happens:** PyMongo's default `BSON ObjectId` type isn't JSON-serializable.
**How to avoid:** In the new `GET /api/v1/alerts` endpoint, project `_id` out (`{"_id": 0}`) at the Mongo find level, OR run a list comprehension that stringifies it (`a['_id'] = str(a['_id'])`).
**Warning signs:** `TypeError: Object of type ObjectId is not JSON serializable` on the alerts list endpoint.

### Pitfall 4: `data-theme` set on body vs html

**What goes wrong:** Tailwind v4's `@custom-variant dark (&:where([data-theme=dark], [data-theme=dark] *))` selects descendants of `[data-theme=dark]`. The current Jinja code sets the attribute on `<body>` (`ghana_cap_dashboard.html:537`). If the React port sets it on `<html>` instead (the more common React pattern), CSS will look correct in isolation but the ported `[data-theme="light"]` block in `index.css` (ported from line 23) won't match because the selector is `[data-theme="light"]` (just the element with the attr, not descendants).
**Why it happens:** Selector specificity / scope mismatch between root selector and theme-attribute placement.
**How to avoid:** Set `data-theme` on **both** `documentElement` and `body` (Pattern 4) for transition safety, AND scope custom properties under `:root[data-theme="light"], [data-theme="light"]` to match either. Or simpler: only set on `documentElement` and write CSS as `:root[data-theme="light"] { ... }`.
**Warning signs:** Toggling theme changes some elements but not others.

### Pitfall 5: Audio links break on dev because Vite doesn't know about `/static`

**What goes wrong:** Alert detail audio elements use `src="/static/audio/alert_xxx.mp3"`. In dev, Vite's `:5173` server doesn't proxy `/static/*` unless explicitly configured.
**Why it happens:** Vite proxy default is no proxying — only matched paths go to Flask.
**How to avoid:** Add `'/static': { target: 'http://localhost:5000' }` to the Vite proxy block (Pattern 1).
**Warning signs:** Audio elements show 404 in the dev tools network tab; console errors `Uncaught (in promise) DOMException: The element has no supported sources.`

### Pitfall 6: Flask-Limiter rate-limits hit during dev hot reload

**What goes wrong:** Phase 2 added `Flask-Limiter` with `default_limits=["200 per hour"]` (`ghana_cap_app.py:104`). When dev sessions exercise endpoints heavily (HMR triggers fetches on every save), the per-IP 200/hour limit can trip.
**Why it happens:** Limiter doesn't differentiate dev vs prod traffic.
**How to avoid:** Keep dev hits below 200/hour OR set `RATELIMIT_ENABLED=False` env var (Flask-Limiter respects this). Phase 4 plan should add `if app.config.get('TESTING') or os.environ.get('FLASK_ENV') == 'development': limiter.enabled = False` (a one-liner) so HMR cycles don't lock out dev.
**Warning signs:** `429 Too Many Requests` in the SPA's fetch calls during hot reload sessions.

### Pitfall 7: Three.js wireframe globe inside React rerenders cause leaks

**What goes wrong:** Today's Three.js setup in the Jinja template runs `initGlobe()` once and `animate()` in a `requestAnimationFrame` loop. Naively porting to React without `useEffect` cleanup creates new scenes/cameras on every parent rerender.
**Why it happens:** React's lifecycle vs Three's imperative scene-graph model.
**How to avoid:** Wrap globe init in `useEffect(() => { ...init(); return () => { renderer.dispose(); cancelAnimationFrame(...) } }, [])`. The simpler path for Phase 4 (since Phase 7 swaps to `react-globe.gl` anyway): keep the globe as plain CSS gradient/blur, defer 3D until Phase 7. Recommend: ship Phase 4 with a static `<div className="globe-bg" />` placeholder (radial gradient + blur), let Phase 7 add the actual globe.
**Warning signs:** Memory profile climbs; multiple WebGL contexts in DevTools; "Maximum call stack size exceeded" on tab switches.

### Pitfall 8: Mixed Vite-base assumption

**What goes wrong:** The SPA's `index.html` references assets as `/assets/index-[hash].js`. If Flask is launched from a different working directory (e.g., gunicorn from `/app`), relative paths resolve wrong.
**Why it happens:** `static_folder` and `template_folder` are resolved relative to `app.root_path` unless given absolute paths.
**How to avoid:** Resolve `DIST_DIR` with `os.path.dirname(os.path.abspath(__file__))` (Pattern 2). Tested under both `python ghana_cap_app.py` (cwd = repo root) and `gunicorn -w 1 ghana_cap_app:app` (cwd may differ).
**Warning signs:** 404s for `/assets/*.js` in production but works in dev.

## Code Examples

### Bootstrap a new Vite + React + TS + Tailwind 4 project under frontend/

```bash
# Source: https://tailwindcss.com/docs/installation/using-vite
# From repo root:
npm create vite@latest frontend -- --template react-swc-ts
cd frontend
npm install
npm install motion socket.io-client clsx tailwind-merge class-variance-authority leaflet react-leaflet lucide-react
npm install -D tailwindcss @tailwindcss/vite @types/leaflet
```

### Minimal vite.config.ts

```typescript
// frontend/vite.config.ts
// Source: https://vite.dev/config/server-options.html + https://tailwindcss.com/docs/installation/using-vite
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      '/api':       { target: 'http://localhost:5000', changeOrigin: true },
      '/socket.io': { target: 'http://localhost:5000', ws: true, changeOrigin: true },
      '/static':    { target: 'http://localhost:5000', changeOrigin: true },
    },
  },
  build: { outDir: 'dist', emptyOutDir: true, sourcemap: true },
})
```

### Minimal Card primitive (with cn + cva)

```typescript
// frontend/src/components/ui/Card.tsx
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '../../lib/cn'
import type { ComponentPropsWithoutRef } from 'react'

const card = cva('glass-card transition-colors', {
  variants: {
    intent: {
      default: '',
      success: 'border-emerald-500/40',
      warning: 'border-amber-500/40',
      danger:  'border-red-500/40',
    },
    padding: { sm: 'p-4', md: 'p-6', lg: 'p-8' },
  },
  defaultVariants: { intent: 'default', padding: 'md' },
})

interface CardProps extends ComponentPropsWithoutRef<'div'>, VariantProps<typeof card> {}

export function Card({ className, intent, padding, ...rest }: CardProps) {
  return <div className={cn(card({ intent, padding }), className)} {...rest} />
}
```

```typescript
// frontend/src/lib/cn.ts
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `tailwind.config.js` JS config | CSS-first `@theme {}` block (no JS file required) | Tailwind v4 (Jan 2025) | All custom tokens become CSS variables; cleaner for shared dark/light schemes. JS config still loadable via `@config` for backward compat. |
| `@tailwind base; @tailwind components; @tailwind utilities;` | `@import "tailwindcss";` | Tailwind v4 | Single import line; smaller mental model. |
| `dark:` class triggered by `class="dark"` on `<html>` | Configurable via `@custom-variant dark (...)` to use `[data-theme=dark]`, `.dark`, or any selector | Tailwind v4 | Matches whichever attribute strategy the existing app uses. |
| `framer-motion` package + `import { motion } from 'framer-motion'` | `motion` package + `import { motion } from 'motion/react'` | Motion 11+ rebrand (2024) | Same code; new canonical name; both packages still publish at parity. |
| Babel-based React HMR (`@vitejs/plugin-react`) | SWC-based HMR (`@vitejs/plugin-react-swc`) | Vite 4+ | ~20x faster transforms; default for `npm create vite@latest` with `react-swc-ts` template. |
| `type=any` for API responses | Hand-rolled `interface CapAlert {}` from server canonical shape | Phase 4 baseline | Compile-time errors when Mongo schema drifts from client expectations. |
| Single namespace Socket.IO | Already split: default + `/live_feed` (Phase 8) | Pre-Phase-4 | The default namespace stays for the dashboard; `/live_feed` stays for the public TV. SPA never touches `/live_feed`. |
| Inline `<script>` with `location.reload()` on `new_alert` | `useAlerts` hook with `setAlerts(prev => ...)` | Phase 4 | True real-time updates; preserves Socket.IO connection across alert events. |

**Deprecated/outdated:**
- **`framer-motion` package name:** still works but redirects in docs to `motion`. Recommend the canonical `motion` import path.
- **`tailwind-variants` library:** community-favored alternative to `cva`. Both work; `cva` has wider adoption.
- **`react-router` for this project:** the SPA is a single-page tabbed UI. No deep links needed in v1. Skip a router; Phase 8 already handles `/public/feed/display` as a separate Jinja page.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | SameSite=Lax cookie + `@csrf.exempt` is acceptable v1 CSRF posture for the operator-facing JSON endpoints | Pattern 7 | If the threat model demands header-CSRF (e.g. shared-IP environments, browsers without strict SameSite), the recommendation needs to flip to token-in-header. User confirmation needed before locking. |
| A2 | Operator browsers meet Tailwind v4's modern-browser bar (Safari 16.4+, Chrome 111+, Firefox 128+) | Standard Stack > Alternatives | If operators run older browsers, Tailwind v3.4 is the safe choice (config in `tailwind.config.js`). |
| A3 | Vite 6.0 (not 8.x) is the canonical line — registry shows 8.0.11 exists but the ecosystem standard for new scaffolds is 6.x | Standard Stack > Core | If 8.x is the new canonical (registry suggests it might be), the scaffolding command should pin `vite@8`. Verify via `npm create vite@latest` output during Wave 0. |
| A4 | `frontend/dist/` will not exceed ~5MB and Flask serving it as a static folder is fine — no CDN required for the v1 deploy | Pattern 2 | If bundle balloons (e.g. Mapbox + react-globe.gl in Phases 5/7 pull in 2-3 MB each), serving via Flask becomes a bottleneck. Re-evaluate at Phase 7. |
| A5 | The Webhook Config "view current key" view does not need to expose the key value (Phase 2 already removed plaintext key display) | Pattern 9 | If operators expect to copy-paste the key from the dashboard, the design needs a secure-reveal flow (re-auth → reveal → auto-hide). |
| A6 | Phase 4 ships without React Router — single-page tabbed UI sufficient for v1 | Recommended Project Structure | If a future "shareable URL" requirement appears (e.g. "send me this alert"), retrofitting react-router across components is moderate cost. |
| A7 | Test Dispatcher uses a server-side proxy endpoint `POST /api/v1/admin/test-dispatch` to keep the GMeT API key out of the browser | Pattern 9 | If the design intends for operators to manage the key themselves (rotate, copy, paste), the proxy approach is wrong and a key-in-browser flow is needed. |
| A8 | The phase brief's "framer-motion" is a name reference, not a hard library pin — `motion` package at the same version is acceptable | Standard Stack > Alternatives | Trivial; both packages are byte-identical. Documented for transparency. |

## Open Questions

1. **Should login.html migrate to React or stay Jinja?**
   - What we know: Phase brief recommends Jinja stays for v1. SMS-2FA flow is a 2-POST form with CSRF and a redirect on success.
   - What's unclear: Whether the design system needs login to also feel SPA-native.
   - Recommendation: Stay Jinja for v1. Re-evaluate after Phase 9 tests confirm the v1 UX is acceptable.

2. **Is there a need for client-side routing (react-router) within the SPA?**
   - What we know: Three tabs today (Pipeline / Manual / Settings), all in-memory state. The PRD §4 adds Webhook Config + Test Dispatcher as additional screens — could be tabs or sub-routes.
   - What's unclear: Whether deep-linking to a specific alert (`/alerts/GH-CAP-A1B2C3D4`) is in scope.
   - Recommendation: No router in v1. If/when deep links are needed, add `react-router-dom@7`.

3. **Webhook key rotation API — full scope or stub?**
   - What we know: REQ-dashboard-webhook-config says "view/generate/revoke." Today's design has one env-var-set key.
   - What's unclear: Whether Phase 4 ships with a real multi-key store + rotation flow, or a stub UI ("Contact admin to rotate").
   - Recommendation: Stub UI in Phase 4 (read-only display + "Contact admin" button), promote to a full key-store in a follow-up phase. The implementation cost (Mongo collection + multi-key hash check + UI flow) is meaningful and not strictly on the Phase 4 critical path.

4. **Existing 27 audio MP3s in static/audio/ — referenced by what alerts?**
   - What we know: Files exist (verified `ls static/audio` returns 27 entries); MongoDB alert documents reference them in `audio_links: { lang: '/static/audio/...' }`.
   - What's unclear: Whether there are orphan files (no longer referenced by any alert doc) or stale references (alert docs pointing at deleted files).
   - Recommendation: No action in Phase 4 (preservation, not cleanup). The SPA renders whatever path the alert doc carries; missing files surface as failed `<audio>` elements, which is fine — the existing dashboard has the same behavior.

5. **Three.js globe: keep, replace with placeholder, or wait for Phase 7?**
   - What we know: Phase 7 explicitly swaps to `react-globe.gl`. Phase 4 should not touch the globe more than necessary.
   - What's unclear: Whether the v1 dashboard ships with a working background or with a static gradient.
   - Recommendation: Static radial-gradient `<div className="bg-globe-placeholder" />` for Phase 4. Saves a working-Three.js port that gets thrown away in Phase 7.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | Vite, npm packages | ✓ | 22.18.0 | — (already meets Vite 6's Node 18+ requirement) |
| npm | Package install | ✓ | 10.9.3 | — |
| Python | Flask backend (existing) | ✓ | 3.13.7 | — |
| Flask 3.0 + Flask-SocketIO 5.3.6 | SPA serving + Socket.IO | ✓ | per requirements.txt | — |
| Vite registry availability | npm install | ✓ | (web reachable) | — |
| Modern browser (Chrome 111+ / Firefox 128+ / Safari 16.4+) | Tailwind v4 features | ✓ assumed for operators | — | Fall back to Tailwind v3.4 if older browsers are required |
| Mapbox token | NOT needed in Phase 4 (Phase 5) | n/a | — | — |
| Anthropic key | NOT needed in Phase 4 (Phase 6) | n/a | — | — |

**Missing dependencies with no fallback:** None for Phase 4.

**Missing dependencies with fallback:** None — all deps are npm-installable; Tailwind v3.4 fallback documented if browser support concerns arise.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework (existing) | pytest 8.x + pytest-flask 1.3 — Python integration suite (Phase 9 backend portion already shipped, 26 tests passing) |
| Framework (new for Phase 4) | Vitest 1.x (recommended) for component unit tests, Playwright (deferred to Phase 9) for E2E |
| Config file | `frontend/vitest.config.ts` (Wave 0); `pytest.ini` / `tests/conftest.py` already exist |
| Quick run command | `pytest tests/ -x` (existing) for backend; `cd frontend && npm test` (Wave 0) for SPA |
| Full suite command | `pytest tests/` (~36s today) + `cd frontend && npm test && npm run build` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| REQ-react-vite-frontend | `frontend/dist/` builds cleanly | smoke | `cd frontend && npm run build` | ❌ Wave 0 |
| REQ-flask-json-api-only | `GET /api/v1/alerts` returns JSON, `GET /` returns SPA HTML, no Jinja-rendered dashboard | integration | `pytest tests/test_endpoints.py::test_dashboard_serves_spa` | ❌ Wave 0 (extend existing test_endpoints.py) |
| REQ-tailwind-glassmorphic-system | `glass-card` utility renders with backdrop-blur | manual / visual | Phase 9 visual regression (Playwright + screenshot) | ❌ Phase 9 |
| REQ-framer-motion-transitions | Tab switch animates with motion's `AnimatePresence` | manual / visual | Phase 9 E2E | ❌ Phase 9 |
| REQ-port-light-dark | Toggle persists to localStorage, applies `data-theme` | unit | `npx vitest src/hooks/useTheme.test.ts` | ❌ Wave 0 |
| REQ-dashboard-active-alerts-view | Alerts render in pipeline tab from `GET /api/v1/alerts` initial fetch + Socket.IO `new_alert` | unit + e2e | Vitest + Phase 9 Playwright | ❌ Wave 0 + Phase 9 |
| REQ-dashboard-webhook-config | Settings tab Webhook Config screen renders read-only key state | unit | Vitest snapshot of WebhookConfig component | ❌ Wave 0 |
| REQ-dashboard-test-dispatcher | Button triggers POST that creates an alert visible in pipeline | integration | `pytest tests/test_endpoints.py::test_admin_test_dispatch` | ❌ Wave 0 |
| REQ-design-language-glassmorphism | `glass-card` matches PRD spec — semi-transparent + backdrop-blur + border + shadow | manual / visual | Phase 9 screenshot regression | ❌ Phase 9 |

### Sampling Rate

- **Per task commit:** `pytest tests/ -x` (existing) + `cd frontend && npm run build` (must succeed)
- **Per wave merge:** `pytest tests/` + `cd frontend && npm test && npm run build`
- **Phase gate:** Full suite green + manual click-through of pipeline / manual / settings / theme toggle / test dispatcher before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `frontend/vitest.config.ts` — Vitest config (jsdom env, `@testing-library/react`)
- [ ] `frontend/src/test/setup.ts` — testing-library setup
- [ ] `frontend/package.json` test script — `"test": "vitest"`
- [ ] `frontend/src/hooks/useTheme.test.ts` — theme persistence + toggle behavior
- [ ] `frontend/src/components/pipeline/AlertCard.test.tsx` — render + expand toggle
- [ ] Extend `tests/test_endpoints.py` — `test_dashboard_serves_spa` (asserts HTML response references `/assets/` URLs after Phase 4 wiring) and `test_alerts_list_endpoint` (new `GET /api/v1/alerts`).
- [ ] Extend `tests/conftest.py` — fixture for testing client that bypasses CSRF (already exists per Phase 9 changelog) — confirm.

*Note:* the existing 26-test pytest suite covers all backend services + integration. Phase 4 only adds a few endpoint-level tests; bulk of Phase 4 quality is Vitest + Phase 9 Playwright/visual.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes | Existing — Email + 6-digit code via SMS 2FA (Phase 2). React frontend redirects to `/login` (Jinja) on 401. |
| V3 Session Management | yes | Existing — Flask `Session` cookie, HttpOnly + SameSite=Lax + Secure-in-prod (Phase 2). React relies on `credentials: 'same-origin'`. |
| V4 Access Control | yes | Existing role checks in `/api/v1/alerts/manual`, `/api/v1/alerts/validate/<identifier>`, `/api/v1/agents/draft`. SPA must show/hide UI based on `user.role` from session — but **never trust the SPA-side check alone** (server enforces). |
| V5 Input Validation | yes | Server enforces (existing). Add client-side validation in Manual Entry form (TypeScript types + `<input required>`) for UX, not security. No `zod` needed for the small surface. |
| V6 Cryptography | yes (transport) | TLS in production (operator concern); React doesn't handle crypto. Session cookie is HMAC-signed by Flask `SECRET_KEY`. |
| V8 Data Protection | yes | Don't store the GMeT API key in the browser (see A5/A7). Don't log session cookies in client console. |
| V13 API & Web Service | yes | All state-changing endpoints are JSON; CSRF stance documented in Pattern 7. Same-origin cookie defense + role checks. |
| V14 Configuration | partial | Vite build outputs source maps (`sourcemap: true`); turn off sourcemaps in production builds for the build artifact (`build.sourcemap: false` for prod) to avoid leaking source structure. |

### Known Threat Patterns for {React + Vite + Flask SPA}

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| XSS via dangerouslySetInnerHTML | Tampering | Don't use it. React escapes by default. CAP description text rendered as `{description}`, not `dangerouslySetInnerHTML`. |
| CSRF on state-changing API | Tampering | SameSite=Lax cookie (existing) + same-origin requirement. Optional header-CSRF deferred. |
| Open redirect via login `next` param | Spoofing | Existing `redirect(url_for('dashboard'))` is hardcoded, not user-controlled. SPA doesn't pass `?next=`. |
| Mixed content (http://localhost in prod build) | Information Disclosure | Use environment-relative URLs; `socket.io-client` `io()` with no URL connects to current origin. No hardcoded `localhost:5000`. |
| Source map disclosure in prod | Information Disclosure | `vite.config.ts` build.sourcemap: false in prod (gate via `process.env.NODE_ENV` or two configs). |
| WebSocket origin spoofing | Spoofing | Existing `cors_allowed_origins` env-driven (Phase 2). Verify dev origin `:5173` is in `ALLOWED_ORIGINS`. |
| Sensitive data in client bundle | Information Disclosure | Don't put secrets in `frontend/.env` files prefixed with `VITE_*` (those leak to client). Backend keeps secrets. |
| Prototype pollution via fetched JSON | Tampering | Treat all `fetch().then(j => j)` as `unknown` and validate before use. Hand-rolled types help, but a runtime `zod` parse on critical paths (alerts list) is cheap insurance — note for follow-up. |

## Project Constraints (from CLAUDE.md)

Per the project's CLAUDE.md, the planner must verify:

- **Active entry point** is `ghana_cap_app.py`, not `app.py`. The Procfile/Dockerfile have been updated in Phase 1 to reference `ghana_cap_app:app`. Phase 4 changes do **not** revert this.
- **`process_alert_logic`** is the single funnel for all alert ingress. Phase 4 must not duplicate this funnel client-side.
- **Workflow stage state machine** (0/1/3) is encoded across `manual_alert` (line 235), validator allowlist (line 250), stage guard at line 261, dispatch gate at line 415. The SPA must read `workflow_stage` from JSON and render the correct badge — but must not invent new stages.
- **Graceful-degradation invariant:** every services/ module checks for credentials and falls back. The frontend must surface mock data the same way the existing dashboard does (e.g., audio_links pointing at `/static/audio/mock_<lang>.mp3` should render the player — let the browser show "broken audio" rather than hide the element).
- **MongoDB Atlas operational store** — Phase 4 adds at most one new endpoint (`GET /api/v1/alerts`) that reads from this; no schema changes.
- **PostgreSQL analytics DB is external** — Phase 4 doesn't touch it.
- **No mock data in dev/prod paths** — mocks are only graceful-degradation fallbacks. The Test Dispatcher injects a fixed mock CAP payload via the existing `gmet_webhook` endpoint — that's a deliberate test fixture, not "mock data." Keep it server-side (Pattern 9) so the boundary is clear.
- **File-size convention (~300-400 lines):** every component file should stay under this. `App.tsx`, `Pipeline.tsx`, `ManualEntry.tsx`, `Settings.tsx` each in their own file; sub-components extracted aggressively.
- **Never overwrite `.env` without confirmation:** Phase 4 should not touch `.env` (it's a backend file). The frontend gets its own `.env.development` only if absolutely needed (and even then: `VITE_*`-prefixed values are public).
- **Hard-coded GMeT webhook key (`gh_cap_poc_key_2026`)** is preserved by Phase 1; Phase 4 does **not** rotate it (that's a future phase). Settings tab shows "configured server-side" placeholder (existing Phase 2 behavior — preserve).

## Sources

### Primary (HIGH confidence)
- [Tailwind CSS v4 Vite installation](https://tailwindcss.com/docs/installation/using-vite) — install steps, plugin pattern, CSS import
- [Tailwind CSS v3 → v4 upgrade guide](https://tailwindcss.com/docs/upgrade-guide) — breaking changes, `@theme`, browser requirements, deprecated config keys
- [Tailwind CSS dark mode](https://tailwindcss.com/docs/dark-mode) — `@custom-variant dark` pattern with `[data-theme=dark]` and `.dark`
- [Vite server.proxy options](https://vite.dev/config/server-options.html) — `ws: true` for Socket.IO, `changeOrigin`, target syntax
- [Vite backend integration](https://vite.dev/guide/backend-integration.html) — manifest pattern, dev vs prod
- [Vite build output configuration](https://vite.dev/guide/build.html) — `outDir`, `base`, asset handling
- [Flask Single-Page Applications pattern](https://flask.palletsprojects.com/en/stable/patterns/singlepageapplications/) — `static_folder`, catch-all route, `app.send_static_file('index.html')`
- [Socket.IO client React guide](https://socket.io/how-to/use-with-react) — singleton, useEffect cleanup, listener registration
- [Socket.IO TypeScript guide](https://socket.io/docs/v4/typescript/) — `ServerToClientEvents` and `ClientToServerEvents` interface pattern
- [Socket.IO client options](https://socket.io/docs/v4/client-options/) — path, transports, reconnection, namespaces
- [Motion (framer-motion) docs](https://motion.dev/docs/react) — confirms `motion` package + `motion/react` import path
- [Motion AnimatePresence](https://motion.dev/docs/react-animate-presence) — `mode="wait"` for tab transitions
- [Flask-WTF CSRF docs](https://flask-wtf.readthedocs.io/en/latest/csrf/) — `csrf_meta_tag`, `X-CSRFToken` header pattern, JSON usage
- npm registry queries (executed 2026-05-09): react@19.2.6, react-dom@19.2.6, typescript@5.9.3, vite@6.0.3 (and 8.0.11 also present), @vitejs/plugin-react-swc@4.3.0, tailwindcss@4.3.0 (published 2026-05-08), @tailwindcss/vite@4.3.0, motion@12.38.0, framer-motion@12.38.0, socket.io-client@4.8.3, clsx@2.1.1, tailwind-merge@3.5.0, class-variance-authority@0.7.1, leaflet@1.9.4, react-leaflet@5.0.0, lucide-react@1.14.0, next-themes@0.4.6
- Codebase grep: `ghana_cap_app.py:369-432` (`process_alert_logic` enriched_alert dict shape), `templates/ghana_cap_dashboard.html:13-31` (existing CSS-variable theme tokens), `:533-540` (theme toggle implementation), `:670-672` (Socket.IO `location.reload` hack)

### Secondary (MEDIUM confidence)
- [Flask SPA discussion (vitejs/vite #14977)](https://github.com/vitejs/vite/discussions/14977) — directory layout patterns
- [Vite + Flask integration tutorial (dev.to)](https://dev.to/tylerlwsmith/build-a-vite-5-backend-integration-with-flask-jch) — practical wiring
- [SWC vs Babel performance comparison (dhiwise.com)](https://www.dhiwise.com/post/maximize-performance-how-swc-enhances-vite-and-react) — perf claim of ~20× faster transforms
- [vitejs/vite-plugin-react-swc README](https://github.com/vitejs/vite-plugin-react-swc) — recommended for new projects
- [next-themes README](https://github.com/pacocoursey/next-themes) — works outside Next.js since v0.3.0

### Tertiary (LOW confidence)
- Various Stack Overflow / dev.to posts on Vite-Flask integration patterns — used for ecosystem discovery only; recommendations cross-verified against Vite + Flask official docs.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — every package version verified against npm registry on 2026-05-09; install commands tested in mental model against official docs.
- Architecture (proxy pattern, Flask SPA serve, Socket.IO hook): HIGH — all four cited from official docs; backend matches existing Phase 2 CORS/CSRF posture.
- Tailwind v4 specifics (`@theme`, `@custom-variant`, `@utility`): HIGH — cited directly from Tailwind v4 docs.
- Motion patterns: HIGH — cited from motion.dev docs.
- CSRF stance recommendation: MEDIUM — security recommendation with documented assumption (A1) about SameSite=Lax sufficiency; user should confirm.
- Webhook Config screen scope: MEDIUM — Phase brief lists view/generate/revoke; current backend supports view only, full rotation needs new endpoints (A5, A7). Recommend stub UI for v1.
- Test infrastructure: MEDIUM — Vitest is standard but not yet present in repo; Wave 0 must scaffold it.

**Research date:** 2026-05-09
**Valid until:** 2026-06-08 (30 days; Tailwind 4.3 just shipped 2026-05-08, may receive patch updates within the window — re-verify if research is older than 30 days when planning starts).
