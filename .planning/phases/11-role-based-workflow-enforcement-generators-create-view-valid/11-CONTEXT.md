# Phase 11: Role-Based Workflow Enforcement - Context

**Gathered:** 2026-06-05
**Status:** Ready for planning
**Source:** User request (express path — decisions captured verbatim from user's feature request)

<domain>
## Phase Boundary

Make the existing role model (CAP generator, CAP validator, Admin) coherent end-to-end. Today the roles exist (seed users in `db.py`, partial checks in `ghana_cap_app.py`: `manual_alert` role check ~line 135, validator allowlist ~line 143) but the workflow does not consistently cover them — the React SPA shows all controls to everyone, and not every mutating endpoint enforces the role matrix.

</domain>

<decisions>
## Implementation Decisions

### Role permission matrix (LOCKED — user-specified)
- **CAP generator** (logged in for one agency): can **create** alerts and **view** alerts. Cannot validate.
- **CAP validator**: can **validate** (approve/reject) alerts and **view** alerts. Cannot create.
- **Admin / Super Admin**: can do **both** (create + validate + view).
- Users belong to an agency (e.g. GMeT, NADMO, NCA); a generator logs in *from one agency*.

### Enforcement layers (LOCKED — user-specified)
- **API-level enforcement** on every alert mutation endpoint: create (manual entry), validate (approve/reject), and lifecycle actions (terminate/extend/resolve) must check the session user's role server-side. View endpoints remain available to all authenticated roles.
- **Frontend gating**: the React SPA must gate UI affordances by the logged-in user's role — hide/disable the Manual Entry creation form for validators, hide validator approve/reject controls for generators, Admins see both.
- **Role exposure to frontend**: expose the session user's role + agency to the SPA (e.g. a `/api/v1/me` endpoint) if not already present, so the frontend can gate without guessing.

### Claude's Discretion
- Where lifecycle actions (terminate/extend) sit in the matrix — recommend: treat as validator/admin actions (they mutate dispatched alert state), but verify against existing behavior and keep generators able to manage their own drafts if that's the current contract.
- Whether agency scoping restricts which alerts a generator/validator can act on (e.g. validators validate only their agency's alerts) — current backend has a validator allowlist by agency; preserve existing agency semantics, don't invent stricter scoping than what exists unless trivial.
- Exact UI treatment (hide vs disable-with-tooltip) — pick one consistent pattern.
- HTTP status for denied actions (401 vs 403) and error shape — follow existing API error conventions.

</decisions>

<specifics>
## Specific Ideas

- Backend already has: role check in `manual_alert`, validator allowlist, `workflow_stage` state machine (0 rejected/draft, 1 pending validation, 3 dispatched). CLAUDE.md warns: if adding role/stage logic, update ALL of — role check in `manual_alert`, validator allowlist, stage guard in `validate_alert`, dispatch gate in `process_alert_logic`.
- Seed users (db.py `seed_users()`): francis@example.com (Admin/NCA), generator@example.com (cap generator/GMeT), validator@example.com (cap validator/GMeT), nadmo_gen@example.com (cap generator/NADMO) — these are the test identities for verifying the matrix.
- Preserve graceful-degradation property of services; do not break the GMeT webhook contract (webhook ingestion is API-key authed, not role-authed — out of scope for role gating).

</specifics>

<canonical_refs>
## Canonical References

- `CLAUDE.md` — workflow_stage state machine + the four places role/stage logic must stay in sync
- `ghana_cap_app.py` — existing role checks and all alert endpoints
- `db.py` — seed users, roles, agencies
- `frontend/src/api/client.ts`, `frontend/src/App.tsx` — SPA auth/session handling entry points

</canonical_refs>

<deferred>
## Deferred Ideas

- Formal RBAC framework / permission tables (STATE.md already defers "Formal RBAC (FR12.1), user-action audit logs" to Milestone 2+) — this phase is role-matrix enforcement with the existing three roles, not a generic RBAC system.

</deferred>

---

*Phase: 11-role-based-workflow-enforcement*
*Context gathered: 2026-06-05 via user-request express path*
