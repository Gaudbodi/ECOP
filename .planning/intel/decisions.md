# Decisions (ADR Intel)

> Per-ADR extraction. Each entry preserves the original decision verbatim with provenance. Synthesis happens downstream in `gsd-roadmapper`.

_No ADRs were ingested in this run. The doc set contained one SPEC, one PRD, and one DOC — no architectural decision records._

---

## Implicit / Inherited Technical Decisions

The following decisions are *not* formal ADRs but are technical commitments that surface from the SPEC, PRD, and current-state DOC. They are recorded here so a future ADR-formalization pass has source material. They are NOT treated as locked.

### IMPLICIT-001: CAP v1.2 as the canonical alert format
- source: PRD.txt §2 ("CAP Processing"), §3.1 ("Extract key CAP elements")
- source: Requirements Document for Unified Emergency Communication Platform.pdf §5.7 NFR14 ("The system shall implement CAP (Common Alerting Protocol) for consistent alert formatting.")
- status: implicit (both SPEC and PRD agree)
- scope: alert message format, payload schema, interoperability with telecom operators

### IMPLICIT-002: Python/Flask backend
- source: PRD.txt §5 Tech Stack ("Backend/API: Python/Flask")
- source: CLAUDE.md ("Flask + Socket.IO backend")
- status: implicit, current-state confirmed
- scope: backend framework choice for the Ghana CAP PoC

### IMPLICIT-003: MongoDB Atlas as operational store
- source: PRD.txt §5 Tech Stack ("Database: Mongodb")
- source: CLAUDE.md §Persistence ("MongoDB Atlas (`fsrp_aggregator` DB) is the operational store")
- status: implicit, current-state confirmed
- scope: operational alert/user/verification persistence for the Ghana CAP PoC
- note: SPEC does not mandate MongoDB — leaves DB choice unspecified

### IMPLICIT-004: External PostgreSQL analytics DB owned by another team
- source: CLAUDE.md §Persistence ("PostgreSQL (schema in `earlywarningdb.sql`) is an external analytics DB owned by another team")
- source: services/external_analytics_service.py (referenced)
- status: implicit, inherited from current-state context
- scope: downstream analytics push target; not part of E-CoP control plane
- note: SPEC and PRD do not specify this — it is a constraint inherited from the operational environment

### IMPLICIT-005: Glassmorphism UI design language
- source: PRD.txt §4 ("Design Language: Glassmorphism")
- source: CLAUDE.md §Frontend ("The design language is glassmorphism per the PRD")
- status: implicit, current-state confirmed
- scope: admin dashboard visual design

### IMPLICIT-006: Workflow-stage state machine (0 / 1 / 3)
- source: CLAUDE.md §"Workflow stages (critical)"
- status: implicit, encoded in current code (`process_alert_logic` line 241 dispatch gate)
- scope: alert lifecycle gating across `manual_alert`, `validate_alert`, and dispatch
- note: NOT in PRD or SPEC — emerged from implementation. PRD §6 acceptance criterion ("MNO endpoint receives within 5 seconds of GMeT trigger") implies *no* such gate for GMeT ingress. See INGEST-CONFLICTS.md INFO entry.

### IMPLICIT-007: Graceful-degradation pattern for external integrations
- source: CLAUDE.md §"Services layer" ("every external integration … checks for credentials on init and falls back to mock/log behavior when absent")
- status: implicit, current-state architectural invariant
- scope: all `services/` modules (geo, enrichment, dispatch, email, external_analytics)
- note: explicitly called out as a property to preserve when editing
