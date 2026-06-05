# Phase 11: Role-Based Workflow Enforcement - Pattern Map

**Mapped:** 2026-06-05
**Files analyzed:** 6 (4 modified, 0 new mandatory, 2 optional new)
**Analogs found:** 6 / 6 (all in-repo — this phase hardens existing patterns rather than introducing new shapes)

> **Headline finding for the planner:** Most of the role-gating infrastructure
> the user is asking for *already exists* and works. `/api/v1/me` is live
> (ghana_cap_app.py:293-299), the frontend already gates tabs (TabNav.tsx),
> validator controls (ValidatorControls.tsx), and lifecycle controls
> (LifecycleControls.tsx) by `user.role`. This phase is primarily about
> **closing the two real gaps** and **making the matrix consistent**:
>
> 1. **Backend gap (the important one):** `manual_alert` (ghana_cap_app.py:384-402)
>    has `@login_required` but **no role check**. A `cap validator` can currently
>    POST a create and — because the stage logic is `1 if role=='cap generator' else 3`
>    — would get an alert dispatched at stage 3. This violates the LOCKED matrix
>    ("validators cannot create"). This is the single most load-bearing fix.
> 2. **Frontend consistency:** ManualEntry tab is hidden from validators in
>    TabNav, but there is no defense-in-depth at the ManualEntry component level
>    and the Manual Entry create-form is not role-guarded if reached directly.
>
> Everything else is verification + small consistency edits. Do NOT build a new
> RBAC framework (explicitly deferred in CONTEXT.md).

## File Classification

| File | New/Mod | Role | Data Flow | Closest Analog | Match Quality |
|------|---------|------|-----------|----------------|---------------|
| `ghana_cap_app.py` → `manual_alert` (L384-402) | modified | route (create) | request-response | `validate_alert` (L404-410) role gate; `dispatcher_test` (L352-353) role gate | exact (in-file) |
| `ghana_cap_app.py` → role helper / decorator | new (optional) | middleware (auth) | request-response | `super_admin_required` (L155-165) | exact (in-file) |
| `frontend/src/components/manual/ManualEntry.tsx` | modified | component | request-response | `ValidatorControls.tsx` (early-return gate); `AdminPanel` gate via TabNav | role-match |
| `frontend/src/components/manual/ManualEntryForm.tsx` | modified (optional) | component (form) | request-response | `ValidatorControls.tsx` `canValidate` gate | role-match |
| `tests/test_endpoints.py` | modified | test | request-response | `test_dispatcher_test_admin_only` (L210-223) | exact (in-file) |
| `frontend/src/components/layout/TabNav.tsx` | verify only | component | request-response | already correct (L21-26) | exact |

## Pattern Assignments

### `ghana_cap_app.py` → `manual_alert` role gate (route, request-response) — PRIMARY FIX

**Analog:** `validate_alert` (ghana_cap_app.py:404-410) and `dispatcher_test` (ghana_cap_app.py:352-353) — both show the established server-side role-check idiom.

**The established role-check idiom (copy this shape):**
```python
# validate_alert, line 409-410
if session['user']['role'] not in ['cap validator', 'Admin']:
    return jsonify({"error": "Unauthorized"}), 403
```
```python
# dispatcher_test, line 352-353
if session['user'].get('role') != 'Admin':
    return jsonify({"error": "Unauthorized"}), 403
```

**Current `manual_alert` (the gap), lines 384-402:**
```python
@app.route('/api/v1/alerts/manual', methods=['POST'])
@csrf.exempt
@login_required
def manual_alert():
    """Manual CAP generation from form"""
    data = request.json
    sender_info = {
        "staff_id": session['user']['staff_id'],
        "name": session['user']['name'],
        "agency": session['user']['agency'],
        "role": session['user']['role']
    }
    # NO ROLE GATE HERE — validators can currently create.
    workflow_stage = 1 if sender_info['role'] == 'cap generator' else 3
    return process_alert_logic(data, sender_info=sender_info, client_ip=request.remote_addr, workflow_stage=workflow_stage)
```

**Pattern to apply:** Insert the role gate immediately after `data = request.json`,
allowing only roles that can create (`cap generator`, `Admin`, `Super Admin`),
denying `cap validator`. Use the exact `403 {"error": "Unauthorized"}` shape so
it matches `validate_alert`/`dispatcher_test` and the frontend's existing
`ApiError` handling (client.ts:42-49 reads `payload.error`).

```python
# Allowed creators per LOCKED matrix: generators + admins. Validators cannot create.
if session['user'].get('role') not in ('cap generator', 'Admin', 'Super Admin'):
    return jsonify({"error": "Unauthorized"}), 403
```

**Note on the stage ternary (line 400):** Once validators are blocked, the
`1 if 'cap generator' else 3` branch only ever sees generator/Admin/Super Admin.
Generators → stage 1 (pending), Admin/Super Admin → stage 3 (direct dispatch).
That preserves the documented state machine (CLAUDE.md:50-54). Do NOT change the
stage semantics — only add the gate above it.

**CLAUDE.md sync obligation (lines 50-54):** "If you add a new role or stage,
update all of: the role check in `manual_alert`, the validator allowlist, the
stage guard in `validate_alert`, and the dispatch gate in `process_alert_logic`."
This phase touches the FIRST of those four. Re-verify the other three still
agree with the matrix (they do today; just confirm in the plan):
- validator allowlist: `validate_alert` L409 `['cap validator', 'Admin']` ✓
- lifecycle allowlist: `_LIFECYCLE_ROLES` L465 `{"cap validator", "Admin", "Super Admin"}` ✓
- dispatch gate: `process_alert_logic` L900 `if workflow_stage == 3` ✓

---

### `ghana_cap_app.py` → optional role-decorator helper (middleware, request-response)

**Analog:** `super_admin_required` (ghana_cap_app.py:155-165) — the canonical
decorator pattern already in the file.

```python
def super_admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        u = session.get('user') or {}
        if u.get('role') != 'Super Admin':
            return jsonify({"error": "forbidden", "detail": "Super Admin role required."}), 403
        return f(*args, **kwargs)
    return decorated
```

**Pattern to apply (Claude's discretion — only if it reduces duplication):** A
parameterized `roles_required(*allowed)` decorator would DRY up the three inline
checks (`manual_alert`, `validate_alert`, `dispatcher_test`) and the two
lifecycle checks. Mirror the `super_admin_required` structure: `@wraps`, read
`session.get('user') or {}`, return `403` on miss.

```python
def roles_required(*allowed):
    """Gate a route to a set of roles. Mirrors super_admin_required (L155)."""
    def wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if (session.get('user') or {}).get('role') not in allowed:
                return jsonify({"error": "Unauthorized"}), 403
            return f(*args, **kwargs)
        return decorated
    return wrapper
```

**Caveat for the planner:** Introducing the decorator means replacing the inline
checks in the SAME change (GEMINI.md convention: "if you must replace, remove the
old implementation in the same change" — CLAUDE.md:107). If the planner prefers
minimal blast radius, keep the inline-check pattern (matching `validate_alert`)
and skip the decorator. Either is acceptable; do not do both.

**Error-shape decision (CONTEXT.md "Claude's Discretion"):** Existing endpoints
use **403** with `{"error": "Unauthorized"}` for role denial (validate_alert L410,
dispatcher_test L353) and **403** with `{"error": "forbidden", "detail": ...}`
for super-admin (L163). For consistency with the alert-mutation endpoints, use
`403 {"error": "Unauthorized"}`. The frontend `ApiError` carries `.status` and
`.payload.error` (client.ts:12-20), so 403 surfaces correctly inline.

---

### `frontend/src/components/manual/ManualEntry.tsx` (component, request-response)

**Analog:** `ValidatorControls.tsx:30-33` (early-return role gate) and
`LifecycleControls.tsx:32-34` (role-array `includes` gate). These are the
canonical frontend role-gate idioms — adopt one consistently.

**Idiom A — single-role early return (ValidatorControls.tsx:30-33):**
```typescript
const canValidate =
  (userRole === 'cap validator' || userRole === 'Admin') &&
  alert.workflow_stage === 1
if (!canValidate) return null
```

**Idiom B — role-array includes (LifecycleControls.tsx:8, 32-34):**
```typescript
const LIFECYCLE_ROLES: Role[] = ['cap validator', 'Admin', 'Super Admin']
// ...
const canActOnLifecycle =
  !!userRole && LIFECYCLE_ROLES.includes(userRole) && alert.workflow_stage === 3
if (!canActOnLifecycle) return null
```

**Pattern to apply:** `ManualEntry` is rendered from `App.tsx:58`
(`{tab === 'manual' && <ManualEntry />}`). Today `App.tsx` does NOT pass `user`
into `ManualEntry`. Two consistent options:

1. **Defense-in-depth (recommended):** Pass `user` from `App.tsx` into
   `ManualEntry` (App.tsx:58 currently passes nothing), then add Idiom B at the
   top of `ManualEntry`:
   ```typescript
   const CREATE_ROLES: Role[] = ['cap generator', 'Admin', 'Super Admin']
   if (!user || !CREATE_ROLES.includes(user.role)) {
     return (/* "You do not have permission to create alerts" empty-state card */)
   }
   ```
   This matches the LifecycleControls array pattern AND the TabNav allowlist
   (`['cap generator', 'Admin', 'Super Admin']` — TabNav.tsx:23), so a validator
   who somehow reaches the tab sees a clean denial instead of a usable form.

2. **Rely on TabNav only:** TabNav.tsx:23 already hides the Manual Entry tab for
   validators. If the planner accepts UX-gating-only (server still enforces via
   the `manual_alert` fix above), no ManualEntry change is needed. The user's
   CONTEXT.md asks for BOTH layers, so prefer option 1.

**Prop-passing pattern (how user flows down):** `App.tsx:35` fetches once
(`useApi<User>('/api/v1/me')`) and passes `user` to `Pipeline` (L57) and
`Settings` (L60) and `AdminPanel` (L59, as `currentUser`). Follow the same prop
name convention — pass `user={user}` to `ManualEntry` exactly like `Pipeline`
(App.tsx:57). Do NOT re-fetch `/api/v1/me` inside ManualEntry (Navbar.tsx:24-26
documents the no-refetch rule).

**UI treatment decision (CONTEXT.md "Claude's Discretion: hide vs disable"):**
The codebase consistently uses **hide** (`return null` in ValidatorControls L33
and LifecycleControls L34; tab filter in TabNav L37-39). Stay consistent: hide
the tab (already done) + render a denial empty-state if the component is reached
directly. Do not introduce disable-with-tooltip — it has no precedent here.

---

### `frontend/src/components/manual/ManualEntryForm.tsx` (component/form, request-response) — optional

**Analog:** `ValidatorControls.tsx` early-return gate. Only relevant if the
planner chooses to gate at the form level rather than the `ManualEntry` wrapper.
Prefer gating at `ManualEntry` (parent) — one gate is cleaner than gating the
inner form (ManualEntryForm.tsx:40 takes no `user` prop today). List here for
completeness; recommend NO change if `ManualEntry` is gated.

---

### `tests/test_endpoints.py` (test, request-response)

**Analog:** `test_dispatcher_test_admin_only` (test_endpoints.py:210-223) — the
canonical role-denial test, and `test_manual_alert_requires_login`
(test_endpoints.py:55-58) — the auth-required test.

**Role-denial test idiom (copy verbatim, lines 210-223):**
```python
def test_dispatcher_test_admin_only(app):
    """Non-Admin sessions get 403."""
    with app.test_client() as c:
        with c.session_transaction() as s:
            s["user"] = {
                "staff_id": "G001",
                "name": "Generator User",
                "agency": "GMeT",
                "role": "cap generator",
                "email": "generator@example.com",
            }
        r = c.post("/api/v1/dispatcher/test")
    assert r.status_code == 403
    assert r.get_json() == {"error": "Unauthorized"}
```

**Patterns to apply (new tests for this phase):**
1. **`test_manual_alert_denies_validator`** — clone L210-223, set
   `role="cap validator"` / `email="validator@example.com"`, POST to
   `/api/v1/alerts/manual` with a minimal body, assert `403` +
   `{"error": "Unauthorized"}`.
2. **`test_manual_alert_allows_generator_pending`** — set role `cap generator`,
   POST, assert `201` and `body["message"] == "Alert submitted for validation"`
   (proves stage 1, mirrors the assertion style at L49).
3. **`test_manual_alert_allows_admin_dispatch`** — reuse `auth_client`
   (Admin, conftest.py:47-58), POST, assert `201` and
   `body["message"] == "Alert dispatched"` (stage 3).
4. **`test_validate_alert_denies_generator`** — clone L210-223 with a generator
   session, POST `/api/v1/alerts/validate/<any-id>`, assert `403` (covers the
   already-existing L409 gate — currently untested).

**Session-injection fixture pattern:** Use the inline
`session_transaction()` block (L213-220) for non-Admin roles; use the
`auth_client` fixture (conftest.py:47) for Admin. Note conftest's
`auth_client` is Admin/NCA, not Super Admin — sufficient for "Admin can both".

---

## Shared Patterns

### Server-side role gate
**Source:** `ghana_cap_app.py:409-410` (`validate_alert`), `:352-353` (`dispatcher_test`), `:491-492` (`terminate_alert`), `:548-549` (`extend_alert`)
**Apply to:** `manual_alert` (the gap). Every alert MUTATION endpoint reads
`session['user']['role']` and returns `403 {"error": "Unauthorized"}` on miss.
View endpoints (`list_alerts` L302, `me` L293) stay `@login_required` only — no
role gate (matches CONTEXT.md "View endpoints remain available to all").
```python
if session['user'].get('role') not in (<allowed roles>):
    return jsonify({"error": "Unauthorized"}), 403
```

### Role matrix (canonical, from CONTEXT.md LOCKED decisions)
| Action | cap generator | cap validator | Admin / Super Admin |
|--------|:-:|:-:|:-:|
| Create (manual) | ✓ (→ stage 1) | ✗ **403** | ✓ (→ stage 3) |
| Validate (approve/reject) | ✗ **403** | ✓ | ✓ |
| Lifecycle (terminate/extend) | ✗ **403** | ✓ | ✓ |
| View (list/me) | ✓ | ✓ | ✓ |
| Test dispatcher | ✗ | ✗ | ✓ (Admin only, L352) |
| User onboarding | ✗ | ✗ | Super Admin only (L162) |

(Lifecycle = validator/admin per existing `_LIFECYCLE_ROLES` L465 — matches
CONTEXT.md "Claude's Discretion: recommend treat as validator/admin actions".)

### Frontend role gate (early-return / array-includes)
**Source:** `ValidatorControls.tsx:30-33`, `LifecycleControls.tsx:8,32-34`, `TabNav.tsx:21-26,37-39`
**Apply to:** `ManualEntry.tsx` (defense-in-depth). Two idioms exist; the
array-`includes` form (LifecycleControls) scales better for multi-role gates.
**Rules-of-hooks caveat (ValidatorControls.tsx:14-22 docstring):** call ALL
hooks BEFORE any `if (!canX) return null`. ManualEntry uses `useState` (L24) —
keep the gate AFTER hooks if any are present, or gate before the component body
if no hooks precede it (ManualEntry has one `useState` — put the role check
either before that single hook with no other hooks, or compute-then-return after).

### `Role` type (single source of truth)
**Source:** `frontend/src/api/types.ts:32`
```typescript
export type Role = 'Super Admin' | 'Admin' | 'cap generator' | 'cap validator'
```
**Apply to:** any new role constant/array in the frontend. Import `Role` from
`../../api/types`; never re-declare string-literal roles.

### `/api/v1/me` role exposure (ALREADY EXISTS — verify, don't rebuild)
**Source:** `ghana_cap_app.py:293-299` + `App.tsx:35` consumer
The endpoint the user asks for ("expose role+agency, e.g. /api/v1/me") is already
live and already consumed. It returns the full `session['user']` (staff_id, name,
agency, role, email). The `User` type (types.ts:93-103) already models it. **No
new endpoint needed** — this is a verification item, not a build item.

### Error handling / API client
**Source:** `frontend/src/api/client.ts:23-55`
`apiFetch` throws `ApiError(status, payload)`; 302→/login is auto-handled
(L37-40). A 403 surfaces as `ApiError` with `.status===403` and
`.payload.error==='Unauthorized'`. Existing components read it via
`e instanceof ApiError ? ... e.payload.error` (AdminPanel.tsx:38-42,
LifecycleControls.tsx:61). New denial-path UI should reuse this — no new error
plumbing.

## No Analog Found

None. Every file in scope has a strong in-repo analog. This phase is pure
hardening/consistency on top of established patterns — there is no novel role,
stage, data flow, or component shape to invent.

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| — | — | — | (none) |

## Metadata

**Analog search scope:** `ghana_cap_app.py`, `db.py`, `frontend/src/api/*`,
`frontend/src/hooks/*`, `frontend/src/components/{layout,pipeline,manual,admin}/*`,
`tests/{test_endpoints.py,conftest.py}`
**Files scanned (read in full):** 18
**Pattern extraction date:** 2026-06-05
