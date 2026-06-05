---
phase: quick-260605-eh8
plan: 01
subsystem: frontend
tags: [css, ui, modal, glassmorphism, accessibility]
requires: []
provides:
  - "glass-dialog @utility (near-opaque modal surface modifier)"
affects:
  - "TerminateDialog (resolve modal)"
  - "ExtendDialog"
  - "ConfirmationModal (manual-entry pre-dispatch review)"
tech-stack:
  added: []
  patterns:
    - "Surface modifier utility layered on top of glass-card (overrides bg+blur only, inherits structure)"
key-files:
  created: []
  modified:
    - frontend/src/index.css
    - frontend/src/components/pipeline/LifecycleDialogs.tsx
    - frontend/src/components/manual/ConfirmationModal.tsx
decisions:
  - "Did NOT change the global --color-glass-bg token or .glass-card — added a narrow glass-dialog modifier so non-modal panels keep their lightweight 7% glass look"
  - "glass-dialog overrides only background + blur; padding/border/radius/shadow inherited from glass-card (modifier always co-applied)"
metrics:
  duration: ~3min
  completed: 2026-06-05
requirements: [EH8-OPACITY]
---

# Quick Task 260605-eh8: Increase Opacity of Resolve / Manual Alert Modals Summary

Added a `glass-dialog` surface modifier (near-solid slate base + stronger blur) and applied it to the resolve modal (TerminateDialog), the sibling Extend dialog, and the manual-entry Confirmation modal, restoring legibility without darkening any non-modal glass panel.

## What Changed

- **`frontend/src/index.css`** — Added a new `@utility glass-dialog` rule immediately after `@utility glass-card`. It overrides only the background (a faint top-light gradient over an opaque `rgb(15 23 42 / 0.92)` slate base) and tightens the blur to `blur(28px) saturate(140%)`. Padding, border, radius, and shadow are deliberately omitted — they are inherited from `glass-card`, with which the modifier is always co-applied. `glass-card`, `glass-navbar`, `glass-item`, and the `--color-glass-bg` token are untouched.
- **`frontend/src/components/pipeline/LifecycleDialogs.tsx`** — Added `glass-dialog` to the `GlassCard` className on both `TerminateDialog` (`glass-dialog w-[30rem] max-w-[90vw]`) and `ExtendDialog` (`glass-dialog w-[34rem] max-w-[92vw]`). The extra class composes cleanly through GlassCard's `cn()` (Tailwind-merge).
- **`frontend/src/components/manual/ConfirmationModal.tsx`** — Added `glass-dialog` to the inner modal `motion.div` while keeping `glass-card` (`glass-card glass-dialog w-full max-w-5xl ...`), so it still inherits structure and now gets the opaque background.

No markup, dialog open/close logic, overlay backdrop classes (`backdrop:bg-black/60`, `cap-overlay bg-slate-950/70`), or inner field styling were changed.

## Verification

- `grep -c "@utility glass-dialog" frontend/src/index.css` → 1 ✓
- `grep -c "glass-dialog" frontend/src/components/pipeline/LifecycleDialogs.tsx` → 2 ✓
- `grep -c "glass-dialog" frontend/src/components/manual/ConfirmationModal.tsx` → 1 ✓
- `npm run build` (tsc -b && vite build) → built cleanly in 34.4s, 2643 modules. The 500 kB chunk-size warning is the pre-existing baseline recorded in STATE.md, not introduced by this change.
- glass-card / glass-navbar / glass-item utilities and the `--color-glass-bg` token confirmed unchanged.

## Commits

- `faa2f1f` — feat(quick-260605-eh8): add glass-dialog opaque modal surface utility
- `52167df` — feat(quick-260605-eh8): apply glass-dialog to resolve/extend/confirm modals

## Deviations from Plan

None — plan executed exactly as written.

## Pending Manual Verification (Task 3 — checkpoint:human-verify)

Task 3 is a non-blocking human-verify checkpoint and was intentionally left for the operator per execution constraints. To clear it:

1. Run the frontend dev server (`cd frontend && npm run dev`) and the backend (`python ghana_cap_app.py`).
2. Log in, open the pipeline, and on a dispatched alert click "Terminate / resolved" — confirm the dialog surface is near-solid and text/fields are clearly legible (page behind no longer bleeds through).
3. Open the "Extend / worsening" dialog on the same alert — confirm it matches the resolve dialog's opacity.
4. In Manual Entry, fill the form and hit confirm to open the pre-dispatch Confirmation modal — confirm its surface is legible and consistent.
5. Glance at non-modal panels (navbar, pipeline cards, settings) — confirm they still look like lightweight glass (unchanged).

Resume signal: type "approved" or describe any modal that still looks too transparent.

## Self-Check: PASSED

- FOUND: frontend/src/index.css (glass-dialog utility present)
- FOUND: frontend/src/components/pipeline/LifecycleDialogs.tsx (2 glass-dialog matches)
- FOUND: frontend/src/components/manual/ConfirmationModal.tsx (1 glass-dialog match)
- FOUND commit: faa2f1f
- FOUND commit: 52167df
