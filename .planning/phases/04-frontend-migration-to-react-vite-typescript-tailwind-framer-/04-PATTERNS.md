# Phase 4: Frontend Migration to React + Vite + TypeScript + Tailwind + framer-motion - Pattern Map

**Mapped:** 2026-05-09
**Files analyzed:** 28 new + 1 modified
**Analogs found:** 24 / 28 (4 net-new, no codebase analog — use RESEARCH.md)

The codebase has no prior React, TypeScript, Vite, Tailwind, or framer-motion code. All analogs are inside two large Jinja+vanilla-JS templates (`templates/ghana_cap_dashboard.html`, `templates/public_feed.html`) plus the Flask app (`ghana_cap_app.py`). The migration is a **pattern port**, not a rewrite — visual + behavioral parity first, structural cleanup second. Every analog citation below is a line range the planner can quote into a plan action.

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `frontend/index.html` | config (HTML shell) | static | `templates/ghana_cap_dashboard.html:1-12, 370-371` | exact (head + body shell) |
| `frontend/vite.config.ts` | config | build | _none_ | no analog |
| `frontend/package.json` | config | build | `requirements.txt` (concept only) | concept-only |
| `frontend/tsconfig.json` | config | build | _none_ | no analog |
| `frontend/tailwind.config.ts` | config | theme | `templates/ghana_cap_dashboard.html:13-31` (`:root` + `[data-theme="light"]`) | role-match |
| `frontend/postcss.config.js` | config | build | _none_ | no analog |
| `frontend/src/index.css` | config (CSS layer) | static | `templates/ghana_cap_dashboard.html:33-367` (full `<style>` block) | exact |
| `frontend/src/main.tsx` | entry | bootstrap | `templates/ghana_cap_dashboard.html:626` (`initGlobe()` boot) | concept-only |
| `frontend/src/App.tsx` | component (shell) | request-response | `templates/ghana_cap_dashboard.html:370-529` (navbar + tab container) | exact (port behavior) |
| `frontend/src/components/Navbar.tsx` | component | request-response | `templates/ghana_cap_dashboard.html:372-391` | exact |
| `frontend/src/components/DashboardShell.tsx` | component | request-response | `templates/ghana_cap_dashboard.html:393-529` | exact |
| `frontend/src/components/ThemeToggle.tsx` | component | event-driven | `templates/ghana_cap_dashboard.html:382-384` (button) + `533-540` (handler) | exact |
| `frontend/src/components/Pipeline.tsx` | component | event-driven (Socket.IO) | `templates/ghana_cap_dashboard.html:395-447` + `669-673` (socket) | exact |
| `frontend/src/components/AlertCard.tsx` | component | request-response | `templates/ghana_cap_dashboard.html:400-444` (single `.alert-item` block) | exact |
| `frontend/src/components/AlertDetail.tsx` | component | request-response | `templates/ghana_cap_dashboard.html:416-443` (`.alert-details` + validator controls) | exact |
| `frontend/src/components/ManualEntry.tsx` | component | request-response (form) | `templates/ghana_cap_dashboard.html:451-501` (form HTML) + `695-724` (submit) | exact |
| `frontend/src/components/MapPanel.tsx` | component | event-driven (map clicks) | `templates/ghana_cap_dashboard.html:676-693` (Leaflet+Draw) | exact |
| `frontend/src/components/Settings.tsx` | component | request-response | `templates/ghana_cap_dashboard.html:504-528` | role-match (port + extend) |
| `frontend/src/components/WebhookConfig.tsx` | component | CRUD | `templates/ghana_cap_dashboard.html:507-514` (read-only display only) | partial — net-new feature |
| `frontend/src/components/TestDispatcher.tsx` | component | request-response | _none_ — feature does not exist | no analog |
| `frontend/src/components/GlassCard.tsx` | component | static | `templates/ghana_cap_dashboard.html:110-116` (`.glass-card` rule) | exact |
| `frontend/src/hooks/useSocket.ts` | hook | event-driven (subscribe) | `templates/ghana_cap_dashboard.html:669-673` + `templates/public_feed.html:397-403` | role-match (consolidate) |
| `frontend/src/hooks/useTheme.ts` | hook | event-driven | `templates/ghana_cap_dashboard.html:533-544` | exact |
| `frontend/src/hooks/useAlerts.ts` | hook | event-driven | `templates/ghana_cap_dashboard.html:669-673` (replace reload hack) | concept-only |
| `frontend/src/hooks/useApi.ts` | hook | request-response | `templates/ghana_cap_dashboard.html:651-667` (handleValidation) + `711-723` (form submit) | role-match |
| `frontend/src/api/client.ts` | utility | request-response | `templates/ghana_cap_dashboard.html:651-667`, `711-723` | role-match (consolidate) |
| `frontend/src/api/alerts.ts` | utility | CRUD | `ghana_cap_app.py:225-297` (manual + validate routes) | role-match (server side) |
| `frontend/src/api/agents.ts` | utility | request-response | `ghana_cap_app.py:340-354` (`/api/v1/agents/draft`) | role-match (server side) |
| `frontend/src/api/public.ts` | utility | request-response | `ghana_cap_app.py:305-321` (`/public/feed/receive`) | role-match (server side) |
| `frontend/src/types/api.ts` | model | static | `ghana_cap_app.py:387-412` (`enriched_alert` dict construction) | exact (mirror schema) |
| `frontend/src/types/cap.ts` | model | static | `ghana_cap_app.py:387-412` + `services/enrichment_service.py:98-135` (translations dict) | exact |
| `frontend/src/lib/glass-card.ts` | utility | static | `templates/ghana_cap_dashboard.html:110-116` | exact |
| `frontend/src/lib/animations.ts` | utility | static | _none_ — framer-motion is net-new | no analog |
| `ghana_cap_app.py` (modify) | route | request-response | `ghana_cap_app.py:201-206` (current `dashboard()` route) | exact (modify in place) |

---

## Pattern Assignments

### Cross-cutting: Theme system (CSS variables)

**Analog:** `templates/ghana_cap_dashboard.html` lines 13-31

```css
:root {
    --bg-color: #020617;
    --glass-bg: rgba(255, 255, 255, 0.08);
    --glass-border: rgba(255, 255, 255, 0.15);
    --accent-color: #0ea5e9;
    --secondary-accent: #8b5cf6;
    --text-color: #f8fafc;
    --navbar-bg: rgba(15, 23, 42, 0.6);
}
[data-theme="light"] {
    --bg-color: #f1f5f9;
    --glass-bg: rgba(255, 255, 255, 0.7);
    --glass-border: rgba(15, 23, 42, 0.1);
    --accent-color: #0284c7;
    --secondary-accent: #7c3aed;
    --text-color: #0f172a;
    --navbar-bg: rgba(255, 255, 255, 0.8);
}
```

**Lift to:**
- `frontend/src/index.css` — keep the literal `:root` + `[data-theme="light"]` blocks verbatim. Tailwind reads them via `theme.extend.colors.bg = 'rgb(var(--bg-color) / <alpha-value>)'` etc., OR (simpler) keep semantic colors as `var(--accent-color)` and reference via `bg-[color:var(--accent-color)]` arbitrary values.
- `frontend/tailwind.config.ts` — `darkMode: ['selector', '[data-theme="dark"]']` so Tailwind's `dark:` modifier maps to the existing `data-theme` attribute (don't introduce a competing `class` strategy that fights the existing toggle behavior).

**What to change:** Hex values stay identical to preserve visual parity. Convert `var(--accent-color)` references to RGB triplet form (`14 165 233`) only if Tailwind's alpha modifiers are needed — otherwise leave as-is.

---

### Cross-cutting: Glassmorphic styling

**Analog:** `templates/ghana_cap_dashboard.html` lines 110-116

```css
.glass-card {
    background: var(--glass-bg);
    border: 1px solid var(--glass-border);
    border-radius: 1rem;
    padding: 2rem;
    backdrop-filter: blur(20px);
}
```

Also the navbar variant at lines 57-68 (`background: var(--navbar-bg)` + same blur), and the alert-item variant at lines 124-137 (smaller radius + hover lift).

**Lift to:** `frontend/src/index.css` under `@layer components`:

```css
@layer components {
    .glass-card {
        @apply rounded-2xl p-8 border;
        background: var(--glass-bg);
        border-color: var(--glass-border);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);  /* keep Safari fallback (public_feed.html:88) */
    }
    .glass-navbar { /* same idea, navbar-bg variant */ }
    .glass-item   { /* alert-item: rounded-xl, transition, hover lift */ }
}
```

Plus `frontend/src/components/GlassCard.tsx` — a thin wrapper that `cn()`s `glass-card` with whatever extra classes the caller passes. Don't introduce CVA variants beyond `card | navbar | item` — the codebase only has these three flavors.

**What to change:** Add the `-webkit-backdrop-filter` line that the dashboard template forgot but `public_feed.html:88` includes. Otherwise pixel-identical.

---

### `frontend/src/hooks/useTheme.ts` (hook, event-driven)

**Analog:** `templates/ghana_cap_dashboard.html` lines 533-544

```javascript
function toggleTheme() {
    const body = document.body;
    const currentTheme = body.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    body.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateGlobeColors(newTheme);
}

// Initialize theme
const savedTheme = localStorage.getItem('theme') || 'dark';
document.body.setAttribute('data-theme', savedTheme);
```

**Lift to React idiom:**
- One `useTheme` hook that reads `localStorage.getItem('theme') || 'dark'` for the initial state, calls `document.body.setAttribute('data-theme', theme)` in a `useEffect` whenever theme changes, and returns `{ theme, toggleTheme }`.
- Apply default theme **before React mounts** to avoid a dark→light flash: put `document.body.setAttribute('data-theme', localStorage.getItem('theme') || 'dark')` in an inline `<script>` in `frontend/index.html` head, mirroring the no-flash trick the current template gets for free.

**What to change:** Drop `updateGlobeColors(newTheme)` here — that coupling lives in Phase 7's globe component. The hook should just emit a theme value; consumers (globe, map tile layer, etc.) subscribe via their own `useTheme` calls.

---

### `frontend/src/hooks/useSocket.ts` (hook, event-driven)

**Analogs:**

1. `templates/ghana_cap_dashboard.html` lines 669-673:
   ```javascript
   const socket = io();
   socket.on('new_alert', (alert) => {
       location.reload();  // anti-pattern; see below
   });
   ```

2. `templates/public_feed.html` lines 397-403 (better — namespaced + functional handler):
   ```javascript
   const socket = io('/live_feed');
   socket.on('connect', () => console.log('public feed connected'));
   socket.on('alert', (alert) => {
       renderAlert(alert);
   });
   ```

**Lift to:** A generic `useSocket(namespace?: string)` hook returning the typed `Socket` instance. Inside, `useEffect` creates `io(namespace)`, returns a cleanup that calls `socket.disconnect()` so React StrictMode double-mount doesn't leak listeners. Plus a `useSocketEvent<T>(socket, eventName, handler)` helper that subscribes on mount and calls `socket.off(eventName, handler)` on cleanup — this is the pattern that makes the `location.reload()` removal safe.

**What to change:** Use the public_feed `io('/live_feed')` namespace pattern (line 398) as the better template. The dashboard's bare `io()` call works too but the namespaced form is forward-compatible with Phase 8's `/live_feed` namespace and any future role-scoped channels.

---

### `frontend/src/components/Pipeline.tsx` + `frontend/src/hooks/useAlerts.ts`

**Analog:** `templates/ghana_cap_dashboard.html` lines 395-447 (server-rendered list) + 669-673 (socket handler that reloads)

Server-rendered loop currently:
```jinja
<div id="alerts-list">
    {% for alert in alerts %}
    <div class="alert-item" data-id="{{ alert.identifier }}" onclick="toggleExpand(this)">
        <div class="alert-summary"> ... </div>
        <div class="alert-details"> ... </div>
    </div>
    {% endfor %}
</div>
```

**Lift to:**
- `useAlerts` hook returns `{ alerts, isLoading, error }`. On mount: `GET /api/v1/alerts` (new JSON endpoint — see Server-side companion below). Subscribes to `new_alert` and `alert_updated` and `setAlerts` immutably (`prev => [newAlert, ...prev]` for `new_alert`, `prev => prev.map(a => a.identifier === updated.identifier ? updated : a)` for `alert_updated`).
- `Pipeline` component maps `alerts` to `<AlertCard alert={a} />`.

**What to change (anti-patterns to kill):**
- **Line 660 `location.reload();`** after `handleValidation` — replace with optimistic update via `useAlerts.updateAlert(identifier, patch)` then reconcile from the `alert_updated` socket event.
- **Line 672 `location.reload();`** in the `new_alert` handler — replace with state prepend.
- **Line 720 `location.reload();`** after manual entry submit — replace with `useAlerts.addAlert(newAlert)` from the response payload + close/reset the form.

**Server-side companion (Phase 4 must add):** A `GET /api/v1/alerts` JSON endpoint in `ghana_cap_app.py` returning `get_all_alerts()` JSON-serialized (mirror the `_id → str` conversion at `ghana_cap_app.py:279-280`). Otherwise the React app has no way to fetch the initial list without scraping the server-rendered HTML.

---

### `frontend/src/components/AlertCard.tsx` (component, request-response)

**Analog:** `templates/ghana_cap_dashboard.html` lines 400-444 (full `.alert-item` block) + 643-645 (`toggleExpand`)

Toggle JS:
```javascript
function toggleExpand(element) {
    element.classList.toggle('expanded');
}
```

CSS-driven expand at lines 146-157:
```css
.alert-details {
    max-height: 0;
    overflow: hidden;
    transition: max-height 0.4s ease, padding 0.3s;
    background: rgba(0, 0, 0, 0.2);
    padding: 0 1.5rem;
}
.alert-item.expanded .alert-details {
    max-height: 500px;
    padding: 1.5rem;
}
```

**Lift to:** Local `useState<boolean>(false)` for `expanded`. Replace the CSS `max-height` trick with framer-motion `<AnimatePresence>` + `<motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.4 }}>` so the height transition works for **any** detail height (the current `max-height: 500px` clips long descriptions).

**Stage badge + status badge:** Lines 189-198 define `.stage-1` (orange), `.stage-3` (green), `.stage-0` (red). Port this as a `<StageBadge stage={alert.workflow_stage} />` component with a small mapping `{ 0: 'Draft/Rejected', 1: 'Pending Review', 3: 'Dispatched' }` lifted from the Jinja template at line 405.

**Validator controls:** Lines 437-442 are conditionally rendered:
```jinja
{% if user.role in ['cap validator', 'Admin'] and alert.workflow_stage == 1 %}
<div class="validator-controls" onclick="event.stopPropagation()">
    <button class="btn-approve" onclick="handleValidation('{{ alert.identifier }}', 'approve')">APPROVE & DISPATCH</button>
    <button class="btn-reject" onclick="handleValidation('{{ alert.identifier }}', 'reject')">REJECT</button>
</div>
{% endif %}
```

Lift the **role + stage gate** verbatim — `user.role in ['cap validator', 'Admin'] && alert.workflow_stage === 1`. Drop the `event.stopPropagation()` — in React, just don't bubble the click; put the buttons inside a wrapping `<div onClick={(e) => e.stopPropagation()}>` if AlertCard's outer `<motion.div>` has its own click handler for expand/collapse.

**What to change:** Replace inline `onclick="handleValidation('{{ alert.identifier }}', 'approve')"` (line 439) with `onClick={() => handleValidation(alert.identifier, 'approve')}` — no string-passing across template boundaries.

---

### `frontend/src/components/ManualEntry.tsx` (component, form)

**Analog:** `templates/ghana_cap_dashboard.html` lines 451-501 (form HTML) + 695-724 (submit handler)

Submit handler:
```javascript
document.getElementById('manual-cap-form').onsubmit = async (e) => {
    e.preventDefault();
    const btn = document.getElementById('submit-manual');
    const originalText = btn.innerText;
    btn.disabled = true; btn.innerText = 'PROCESSING...';

    const payload = {
        headline: document.getElementById('headline').value,
        severity: document.getElementById('severity').value,
        urgency: document.getElementById('urgency').value,
        description: document.getElementById('description').value,
        instruction: document.getElementById('instruction').value,
        latitude: document.getElementById('lat').value,
        longitude: document.getElementById('lon').value
    };

    try {
        const res = await fetch('/api/v1/alerts/manual', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const result = await res.json();
        if (res.ok) {
            alert(result.message);
            location.reload();
        }
    } catch (err) { alert('SUBMISSION FAILED'); }
    finally { btn.disabled = false; btn.innerText = originalText; }
};
```

**Lift to:** Controlled inputs in a single `formState` object (use `useState<ManualAlertForm>` or `react-hook-form` if added; the codebase has no precedent so default to plain `useState` — no new dep without need). On submit:
1. Set `isSubmitting = true`, button shows `PROCESSING...`.
2. POST `/api/v1/alerts/manual` via `apiClient.post('/alerts/manual', payload)` — see `client.ts` below.
3. On success: toast (replace `alert(result.message)`), do **not** `location.reload()` — the `new_alert` socket event will refresh the Pipeline tab automatically.
4. On error: surface the error in a `<div role="alert">` next to the submit button (replace `alert('SUBMISSION FAILED')`).
5. `finally` block restores button state — keep this pattern.

**Field shape (what the API expects, do not change):** `headline`, `severity`, `urgency`, `description`, `instruction`, `latitude`, `longitude`. Plus the lat/lon-tolerance contract in `ghana_cap_app.py:357-366` — empty strings are OK, the server defaults to Accra coords. So lat/lon can stay optional in the React types.

**What to change:** Drop the `document.getElementById('lat').value` pattern entirely. The map writes lat/lon via the React state setter, not by mutating hidden inputs.

---

### `frontend/src/components/MapPanel.tsx` (component, event-driven)

**Analog:** `templates/ghana_cap_dashboard.html` lines 676-693

```javascript
const map = L.map('map').setView([7.9465, -1.0232], 7);
L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png').addTo(map);

const drawnItems = new L.FeatureGroup();
map.addLayer(drawnItems);
const drawControl = new L.Control.Draw({
    draw: { polyline: false, circlemarker: false },
    edit: { featureGroup: drawnItems }
});
map.addControl(drawControl);

map.on(L.Draw.Event.CREATED, function (e) {
    drawnItems.clearLayers();
    drawnItems.addLayer(e.layer);
    const latlng = e.layer.getLatLng ? e.layer.getLatLng() : e.layer.getBounds().getCenter();
    document.getElementById('lat').value = latlng.lat;
    document.getElementById('lon').value = latlng.lng;
});
```

**Lift to:** A thin React wrapper. **Do not** use `react-leaflet` — adding it conflicts with Phase 5's planned Mapbox swap. Instead:
- `useEffect(() => { ... }, [])` initializes Leaflet imperatively against a `useRef<HTMLDivElement>` container. Cleanup calls `map.remove()`.
- Replace the `document.getElementById('lat').value = …` lines with a callback prop: `<MapPanel onLocationChange={(lat, lon) => setForm(f => ({ ...f, latitude: lat, longitude: lon }))} />`.

**Theme-aware tile URL:** Currently hard-coded to `dark_all` (line 677). Read `useTheme()` and switch to `light_all` when `theme === 'light'`. The `public_feed.html:334` uses the same `dark_all` URL — Phase 4 picks the same default but makes it reactive.

**What to change:** Tab-switch resize fix at line 640 (`setTimeout(() => map.invalidateSize(), 100)` after switching to manual tab) — port this. Leaflet maps initialized while their container has `display: none` need an `invalidateSize()` once the container becomes visible. In React: `useEffect(() => { if (visible) map.invalidateSize() }, [visible])`.

---

### `frontend/src/components/Settings.tsx` + `WebhookConfig.tsx` + `TestDispatcher.tsx`

**Analog (Settings only):** `templates/ghana_cap_dashboard.html` lines 504-528

```jinja
<div id="settings" class="tab-content">
    <div class="glass-card">
        <h2>Platform Configuration</h2>
        <div class="form-group">
            <label>Ingress Webhook Endpoint (GMeT)</label>
            <div style="background: rgba(0,0,0,0.3); ...">
                <script>document.write(window.location.origin + '/api/v1/alerts/gmet/webhook')</script>
            </div>
            <div>Required Header: X-CAP-API-KEY: (configured server-side; rotate via env var GMET_WEBHOOK_API_KEY)</div>
        </div>
        <!-- SMS Provider + Enrichment Engine cards: read-only status badges -->
    </div>
</div>
```

**Lift to:** Three sub-components inside `Settings.tsx`:
1. **`<WebhookConfig />`** — replaces the read-only display with view/generate/revoke (PRD §4 + ROADMAP success criterion #5). The current implementation only displays the URL; the new one reads/writes the key. **Server-side companion required:** add `GET /api/v1/admin/webhook-key`, `POST /api/v1/admin/webhook-key/rotate`, `DELETE /api/v1/admin/webhook-key` (all `@login_required`, role-gated to Admin; CSRF-exempt JSON pattern from `ghana_cap_app.py:225-227`).
2. **`<TestDispatcher />`** — net-new, no analog (ROADMAP success criterion #6). Button injects a mock GMeT JSON payload and POSTs it to `/api/v1/alerts/gmet/webhook` with the configured `X-CAP-API-KEY` header. Use `process_alert_logic`'s `enriched_alert` shape (`ghana_cap_app.py:387-412`) as the mock payload contract.
3. **`<ProviderStatus />`** — the existing SMS Provider + Enrichment Engine cards (lines 515-526). Pure read-only; render the same "CONFIGURED" badge from line 519. Could become reactive via a `GET /api/v1/system/health` endpoint that pings each provider, but Phase 4 can ship the static badge.

**Anti-pattern to kill:** Line 511 `<script>document.write(window.location.origin + '/api/v1/alerts/gmet/webhook')</script>` — replace with a plain React expression: `{`${window.location.origin}/api/v1/alerts/gmet/webhook`}`. `document.write` after page load erases the document; it only "works" here because the script runs before close-of-body parsing.

---

### `frontend/src/api/client.ts` (utility, request-response)

**Analogs:**
- `templates/ghana_cap_dashboard.html` lines 651-667 (validation POST):
  ```javascript
  const res = await fetch(`/api/v1/alerts/validate/${identifier}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action, reason })
  });
  const result = await res.json();
  if (res.ok) { alert(result.message); location.reload(); }
  else { alert(result.error); }
  ```
- Lines 711-723 (manual submit, same shape).

**Lift to:** A typed wrapper with a single source of truth for base URL, headers, and error parsing.

```typescript
// pseudocode for the planner
async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
    const res = await fetch(path, {
        credentials: 'same-origin',  // session cookie auth (see CSRF section below)
        headers: { 'Content-Type': 'application/json', ...init?.headers },
        ...init,
    });
    if (!res.ok) throw new ApiError(res.status, await res.json().catch(() => ({})));
    return res.json() as Promise<T>;
}
```

**What to change:** Drop `alert()` calls. The hook layer (`useApi`) catches `ApiError` and returns `{ error }` so the component can render an inline error.

---

### CSRF + auth pattern (cross-cutting)

**Analog:** `ghana_cap_app.py` lines 95-97 + JSON endpoint markers at 209, 226, 246, 306, 341.

Current setup:
- `csrf = CSRFProtect(app)` enforces CSRF on all POSTs **except** routes decorated with `@csrf.exempt`.
- All JSON API endpoints (`/api/v1/alerts/manual`, `/api/v1/alerts/validate/<id>`, `/api/v1/agents/draft`, `/public/feed/receive`) are already `@csrf.exempt`. Login (`/login`, form-based) keeps CSRF.

**What this means for the React app:**
- The React app uses **session-cookie auth** — Flask sets the session cookie at login (still Jinja form-based, see `templates/login.html:103`), the React app inherits it via `credentials: 'same-origin'` on every fetch.
- **No CSRF token needed in JSON requests** — the JSON endpoints are already exempt and will stay that way. Document this clearly in `client.ts` so future contributors don't add a token-in-header assumption.
- **Login stays Jinja.** `templates/login.html` keeps `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">` (line 103). Phase 4 does **not** migrate login. Flask's `dashboard()` route (`ghana_cap_app.py:201-206`) becomes the React entry point; `/login` remains server-rendered.
- **Logout** is `GET /logout` (line 196). React renders it as `<a href="/logout">` exactly like the current dashboard at line 389 — no special handling.

**Origin allowlist:** `ghana_cap_app.py:75-77` already includes `http://localhost:5173` (Vite dev) in `ALLOWED_ORIGINS`. Keep that line — Vite dev server proxies/CORS depend on it.

---

### Server-side modification: `ghana_cap_app.py`

**Analog:** Current `dashboard()` at lines 201-206:

```python
@app.route('/')
@login_required
def dashboard():
    """Admin Dashboard View with Tabs"""
    alerts = get_all_alerts()
    return render_template('ghana_cap_dashboard.html', alerts=alerts, user=session['user'])
```

**Modify to:** Serve the Vite-built React shell after `npm run build` produces `frontend/dist/`. Two concrete options for the planner to choose:

1. **Static-file approach (preferred — minimal Flask diff):**
   ```python
   from flask import send_from_directory
   FRONTEND_DIST = os.path.join(os.path.dirname(__file__), 'frontend', 'dist')

   @app.route('/')
   @login_required
   def dashboard():
       return send_from_directory(FRONTEND_DIST, 'index.html')

   @app.route('/assets/<path:filename>')
   def frontend_assets(filename):
       return send_from_directory(os.path.join(FRONTEND_DIST, 'assets'), filename)
   ```
   The React app reads `user` and `alerts` via new JSON endpoints (`GET /api/v1/me`, `GET /api/v1/alerts`) instead of Jinja context.

2. **Render-as-template approach:** keep `render_template('index.html', user=session['user'])` and have Vite output to Flask's `templates/` dir with `<script type="module" src="/assets/index-{hash}.js">`. More fragile because Flask's `templates/` is Jinja-parsed; not recommended.

The `ROADMAP.md:91` success criterion locks option 1 ("Flask serves `dist/index.html` at `/` and `dist/assets/*` under `/assets/`"). Plan accordingly.

**New JSON endpoints required (Phase 4 must add):**
- `GET /api/v1/me` → `jsonify(session['user'])` for the navbar user-name + role-gating in React.
- `GET /api/v1/alerts` → `jsonify([_serialize_alert(a) for a in get_all_alerts()])` where `_serialize_alert` does the `_id → str` conversion seen at `ghana_cap_app.py:279-280`.

Both `@login_required`, both `@csrf.exempt` (matching the JSON-endpoint pattern at lines 209, 226, 246).

---

## Shared Patterns

### Login_required gate (server side)

**Source:** `ghana_cap_app.py` lines 112-118
```python
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function
```

**Apply to:** Every new JSON endpoint Phase 4 adds (`/api/v1/me`, `/api/v1/alerts`, `/api/v1/admin/webhook-key`, etc.). React-side: a 302 to `/login` from a JSON fetch surfaces as a CORS/redirect followed by an HTML response — the API client should detect `res.redirected || res.headers.get('content-type')?.startsWith('text/html')` and trigger `window.location.href = '/login'`.

### Role gate (server + client)

**Source:** `ghana_cap_app.py:250-251` (server)
```python
if session['user']['role'] not in ['cap validator', 'Admin']:
    return jsonify({"error": "Unauthorized"}), 403
```

**Source:** `templates/ghana_cap_dashboard.html:376` + `437` (Jinja render-time gate)
```jinja
{% if user.role in ['cap generator', 'Admin'] %}
{% if user.role in ['cap validator', 'Admin'] and alert.workflow_stage == 1 %}
```

**Apply to:** React mirrors these checks in component-level guards:
```tsx
{user.role === 'cap generator' || user.role === 'Admin' && <ManualEntryTab />}
{(user.role === 'cap validator' || user.role === 'Admin') && alert.workflow_stage === 1 && <ValidatorControls />}
```

The server still enforces — React's gate is UX-only. CLAUDE.md (line 47) lists the four touchpoints any new role requires; planner must update those plus the equivalent React conditionals.

### Alert document shape (typing)

**Source:** `ghana_cap_app.py` lines 387-412 + `services/enrichment_service.py:98-135`

```python
enriched_alert = {
    "identifier": alert_id,
    "sender_name": sender_info.get('name'),
    "sender_agency": sender_info.get('agency'),
    "sender_id": sender_info.get('staff_id'),
    "sender_ip": client_ip,
    "sent": datetime.now(timezone.utc).isoformat(),
    "status": "Actual",
    "msgType": "Alert",
    "scope": "Public",
    "category": "Met",
    "event": "Weather Alert",
    "urgency": "Immediate",
    "severity": "Severe",
    "certainty": "Observed",
    "headline": "Emergency Alert",
    "description": english_text,
    "instruction": "",
    "affected_regions": affected_regions,         # string[]
    "translations": translations,                 # { English: str, Twi: str, Hausa: str }
    "audio_links": audio_links,                   # { English: "/static/audio/…mp3", ... }
    "geo": {"lat": lat, "lon": lon},
    "mno_dispatched": False,
    "sms_sent": False,
    "workflow_stage": workflow_stage              # 0 | 1 | 3
}
```

**Apply to:** `frontend/src/types/api.ts` and `frontend/src/types/cap.ts` — mirror this shape exactly. Workflow stage is `0 | 1 | 3` (literal union, no `2`). `translations` and `audio_links` are `Record<'English' | 'Twi' | 'Hausa', string>` plus optional extra keys for future languages.

### User session shape

**Source:** `ghana_cap_app.py:179-185`
```python
session['user'] = {
    "staff_id": user['staff_id'],
    "name": user['name'],
    "agency": user['agency'],
    "role": user['role'],
    "email": user['email']
}
```

Roles in use: `'Admin'` | `'cap generator'` | `'cap validator'` (see `db.py:57, 69, 79, 89`). Mirror exactly in `frontend/src/types/api.ts`.

### Severity / status badge mapping

**Source:** `templates/public_feed.html:294-301` (more complete than the dashboard's stage-only version)
```javascript
function severityClass(sev) {
    const s = (sev || '').toLowerCase();
    if (s.includes('extreme')) return 'severity-badge sev-extreme';
    if (s.includes('severe'))  return 'severity-badge sev-severe';
    if (s.includes('moderate'))return 'severity-badge sev-moderate';
    if (s.includes('minor'))   return 'severity-badge sev-minor';
    return 'severity-badge sev-default';
}
```

Plus the color values at `public_feed.html:111-115`:
```css
.sev-extreme { background: #b91c1c; }
.sev-severe  { background: #ea580c; }
.sev-moderate { background: #ca8a04; }
.sev-minor   { background: #16a34a; }
.sev-default { background: linear-gradient(135deg, var(--accent), var(--accent-2)); }
```

**Apply to:** `frontend/src/components/SeverityBadge.tsx`. Reuse the substring-match logic — CAP severity values are case-sensitive `'Extreme' | 'Severe' | 'Moderate' | 'Minor' | 'Unknown'` per the form options at `ghana_cap_dashboard.html:463-468`, but the public-feed mapping is defensive against arbitrary casing, which is the safer pattern.

---

## Anti-patterns to NOT Carry Over

These are explicit holdovers from the PoC dashboard that the React migration must replace, not preserve. Each is referenced by a success criterion in `ROADMAP.md:90-99`:

| Anti-pattern | Location | Replace With |
|--------------|----------|--------------|
| `location.reload()` after every Socket.IO event | `ghana_cap_dashboard.html:660, 672, 720` | Reactive state update via `useAlerts` hook (ROADMAP success criterion #2) |
| `<script>document.write(...)</script>` for webhook URL | `ghana_cap_dashboard.html:511` | Plain JSX expression `{`${window.location.origin}/api/v1/alerts/gmet/webhook`}` |
| Inline `onclick="…"` handlers throughout | `ghana_cap_dashboard.html:375, 377, 379, 382, 400, 438, 439, 440, 496` | React `onClick={…}` props with closures over component state |
| `alert(result.message)` and `alert(result.error)` | `ghana_cap_dashboard.html:659, 662, 665, 719, 722` | Toast component (Phase 4 picks one — `sonner` or `react-hot-toast`; codebase has no precedent) or inline error banner inside the form |
| `document.getElementById('lat').value = latlng.lat` | `ghana_cap_dashboard.html:691-692` | Callback prop on `<MapPanel onLocationChange={(lat, lon) => …} />` lifts to controlled form state |
| `prompt('Reason for rejection:')` | `ghana_cap_dashboard.html:648` | A modal/dialog component with a textarea |
| Tab switching via `classList.add('active')` + `display: none` | `ghana_cap_dashboard.html:629-641` | React Router (`/`, `/manual`, `/settings`) OR a `useState` tab switcher inside `App.tsx`. Either is fine — pick by whether deep-linkable URLs are needed (probably yes for `/settings/webhook` etc.). |
| Tab tag-text-substring-matching to find active tab | `ghana_cap_dashboard.html:635-638` (`if(t.innerText.toLowerCase().includes(tabId.substring(0,3)))`) | Just compare `tabId === currentTab` — never match by text content |
| Three.js boot inline at module scope | `ghana_cap_dashboard.html:546-626` | Defer to Phase 7 globe revamp; Phase 4 ships **without** the globe (or with a simple CSS gradient placeholder so the navbar isn't on a flat color). Don't re-port the random-Bezier wireframe. |

---

## No Analog Found

| File | Role | Data Flow | Reason / Mitigation |
|------|------|-----------|---------------------|
| `frontend/vite.config.ts` | config | build | Vite is net-new — use RESEARCH.md scaffold; ensure `server.port = 5173` matches `ghana_cap_app.py:76` ALLOWED_ORIGINS |
| `frontend/tsconfig.json` | config | build | TS is net-new — use Vite React-TS template defaults |
| `frontend/postcss.config.js` | config | build | PostCSS for Tailwind is net-new — standard Tailwind v3 boilerplate |
| `frontend/src/lib/animations.ts` | utility | static | framer-motion presets are net-new; create a small palette: `fadeIn`, `slideUp`, `expand`, `tabTransition`. Keep durations consistent with existing CSS transitions (`0.4s` for expand at `ghana_cap_dashboard.html:149`, `0.2s` for hovers at line 81) |
| `frontend/src/components/TestDispatcher.tsx` | component | request-response | Test dispatcher is a net-new PRD §4 feature; mock payload shape mirrors `enriched_alert` from `ghana_cap_app.py:387-412` |
| `frontend/src/components/WebhookConfig.tsx` | component | CRUD | View/generate/revoke is net-new; current Settings tab only displays the URL (`ghana_cap_dashboard.html:511`). Server-side endpoints to be planned alongside |

---

## Metadata

**Analog search scope:** `templates/`, `services/`, `ghana_cap_app.py`, `db.py`, `static/main.js`, `.planning/ROADMAP.md`, `CHANGELOG.md`, `CLAUDE.md`
**Files scanned:** 9 source files + 4 planning docs
**Pattern extraction date:** 2026-05-09
**Source repo state:** Git branch `main`; latest commit `4f0882b` ("Initial production-ready commit for E-CoP platform"); modified `requirements.txt`; phases 1, 2, 3, 6, 8, 9 already landed per CHANGELOG; phases 4, 5, 7, 10 pending.
