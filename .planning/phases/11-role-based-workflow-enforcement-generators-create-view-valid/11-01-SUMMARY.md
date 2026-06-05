---
phase: 11-role-based-workflow-enforcement
plan: "01"
subsystem: backend-api
tags:
  - role-enforcement
  - security
  - api-gating
  - workflow-stages
dependency_graph:
  requires: []
  provides:
    - server-side create-role gate on manual_alert
    - regression tests for create/validate/lifecycle role matrix
  affects:
    - ghana_cap_app.py
    - tests/test_endpoints.py
tech_stack:
  added: []
  patterns:
    - inline role gate matching validate_alert/dispatcher_test idiom
    - session_transaction() injection for non-Admin role tests
key_files:
  created: []
  modified:
    - ghana_cap_app.py
    - tests/test_endpoints.py
decisions:
  - "Inline role check used (not roles_required decorator) to minimise blast radius and match validate_alert/dispatcher_test idiom per PATTERNS.md"
  - "workflow_stage ternary unchanged: 1 if 'cap generator' else 3 — once validators blocked, else only sees Admin/Super Admin which correctly maps to stage 3"
  - "Resolve confirmed as CAP Cancel alias for terminate; no orphan route exists (grep confirmed 0 hits for def resolve_alert and '/resolve')"
  - "test_dashboard_serves_spa pre-existing failure confirmed and documented; unrelated to this plan (requires npm run build)"
metrics:
  duration: "~15 minutes"
  completed: "2026-06-05"
  tasks_completed: 2
  tasks_total: 2
---

# Phase 11 Plan 01: Server-Side Create-Role Gate + Role-Matrix Tests Summary

**One-liner:** 403 role gate on manual_alert blocks cap validator from creating/dispatching alerts, five endpoint tests lock the full create/validate/lifecycle matrix.

## Tasks Completed

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Add server-side create-role gate to manual_alert + re-verify four sync points | 4d7aa4c | ghana_cap_app.py |
| 2 | Add role-matrix endpoint tests (create-denial, create-allow, validate-denial, lifecycle-denial) | f203357 | tests/test_endpoints.py |

## What Was Built

### Task 1: Server-Side Create-Role Gate

Inserted a role gate in `manual_alert` (ghana_cap_app.py:384-402) immediately after `data = request.json`, before the `sender_info` dict and `workflow_stage` ternary:

```python
# Four-place role/stage matrix sync point #1 (CLAUDE.md): only cap generator,
# Admin, and Super Admin may create alerts. cap validator is denied 403 here.
if session['user'].get('role') not in ('cap generator', 'Admin', 'Super Admin'):
    return jsonify({"error": "Unauthorized"}), 403
```

The `workflow_stage = 1 if sender_info['role'] == 'cap generator' else 3` ternary was left unchanged per plan instructions — once validators are blocked, the else branch only ever sees Admin/Super Admin, which correctly maps to stage 3.

**Four sync points verified (CLAUDE.md obligation):**
- `manual_alert` — new gate added (this task)
- `validate_alert` L409: `['cap validator', 'Admin']` — confirmed matrix-consistent, no edit needed
- `_LIFECYCLE_ROLES` L465: `{"cap validator", "Admin", "Super Admin"}` applied to both terminate_alert (L491) and extend_alert (L548) — confirmed, no edit needed
- `process_alert_logic` dispatch gate L900: `if workflow_stage == 3` — confirmed, no edit needed

**Resolve alias confirmed:** `grep` found zero hits for `def resolve_alert` and `'/resolve'` in ghana_cap_app.py. The "resolve" concept is covered by the terminate endpoint (CAP Cancel), which is already gated by `_LIFECYCLE_ROLES`.

### Task 2: Role-Matrix Endpoint Tests

Five new tests added to `tests/test_endpoints.py` under `# Phase 11: role-matrix enforcement tests`:

1. **`test_manual_alert_denies_validator`** — `cap validator` session, POST /api/v1/alerts/manual, asserts 403 + `{"error": "Unauthorized"}` (REQ-role-matrix-create-gate)
2. **`test_manual_alert_allows_generator_pending`** — `cap generator` session, POST, asserts 201 + `"Alert submitted for validation"` proving stage 1 (REQ-role-matrix-create-gate)
3. **`test_manual_alert_allows_admin_dispatch`** — `auth_client` (Admin), POST, asserts 201 + `"Alert dispatched"` proving stage 3 (REQ-role-matrix-create-gate)
4. **`test_validate_alert_denies_generator`** — `cap generator` session, POST /api/v1/alerts/validate/NONEXISTENT-ID, asserts 403 before 404 path (REQ-role-matrix-validate-gate)
5. **`test_terminate_alert_denies_generator`** — `cap generator` session, POST /api/v1/alerts/NONEXISTENT-ID/terminate, asserts 403 before 404 path (REQ-role-matrix-lifecycle-gate)

All five use the `session_transaction()` inline injection idiom cloned from `test_dispatcher_test_admin_only` (L210-223) for non-Admin roles, and the `auth_client` fixture for Admin.

## Verification Results

```
# Five targeted tests:
5 passed, 26 deselected in 40.28s

# Full suite:
42 passed, 1 failed (pre-existing), 1 skipped in 97.73s
```

**Pre-existing failure:** `test_dashboard_serves_spa` fails because `frontend/dist` is not built in this environment (requires `cd frontend && npm run build`). Confirmed pre-existing by stashing changes and running — same failure before this plan's changes. This is out of scope.

## Deviations from Plan

None — plan executed exactly as written. The inline role-check pattern was used as specified (no roles_required decorator), matching validate_alert and dispatcher_test idioms.

## Known Stubs

None — no stub patterns introduced. The role gate is complete server-side enforcement.

## Threat Flags

No new network endpoints, auth paths, or schema changes introduced. The change closes threat T-11-01 (elevation of privilege via missing manual_alert role gate) and locks T-11-02 and T-11-03 with regression tests. No new threat surface added.

## Self-Check: PASSED

- ghana_cap_app.py: gate exists at the correct location, verified by `python -c "import ast,sys; ..."` exiting 0
- App boots without error: `python -c "import ghana_cap_app"` exits 0 (MongoDB connected, users synchronized)
- Commit 4d7aa4c exists: `git log --oneline -3` confirms feat(11-01) commit
- Commit f203357 exists: `git log --oneline -3` confirms test(11-01) commit
- 5 new tests pass as verified by pytest run above
