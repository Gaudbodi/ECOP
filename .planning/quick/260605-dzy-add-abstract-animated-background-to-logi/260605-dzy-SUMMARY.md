---
phase: quick-260605-dzy
plan: 01
subsystem: auth-ui
tags: [login, css-animation, glassmorphism, jinja]
requires: []
provides:
  - "Animated glassmorphism background behind the Flask login/verification card"
affects:
  - templates/login.html
tech-stack:
  added: []
  patterns:
    - "Pure-CSS @keyframes animation (transform/opacity only) with prefers-reduced-motion guard"
key-files:
  created: []
  modified:
    - templates/login.html
decisions:
  - "Implemented the backdrop as a single fixed .login-bg layer with ::before/::after blobs plus one .login-bg-extra child — three soft radial-gradient blobs, no script, no deps"
  - "Animated only transform + opacity (with will-change) for GPU compositing; never animated background-position/box-shadow/filter on the blobs"
  - "Reused existing cyan (#38bdf8) / indigo (#818cf8) / violet (#8b5cf6) palette against #0f172a; peak blob opacity 0.10-0.16 so the card stays the focal point"
metrics:
  duration: ~6min
  completed: 2026-06-05
---

# Quick Task 260605-dzy: Add Abstract Animated Background to Login Summary

Added a pure-CSS, low-saturation animated glassmorphism backdrop (three drifting cyan/indigo/violet radial-gradient blobs) behind the Flask-served login + verification-code card in `templates/login.html`, honoring `prefers-reduced-motion` and introducing no scripts or dependencies.

## What Was Done

### Task 1: Pure-CSS animated glassmorphism background (commit `bbcef86`)
- Inserted a `<div class="login-bg" aria-hidden="true">` (with a nested `.login-bg-extra` blob) as the first child of `<body>`, painted at `z-index: 0` behind the card.
- Gave `.login-card` `position: relative; z-index: 1;` so it always paints above the backdrop. Added `overflow: hidden` to `body` so off-screen blobs don't create scrollbars.
- Three soft radial-gradient blobs:
  - `.login-bg::before` — cyan, top-left, `blobDriftA` (22s)
  - `.login-bg::after` — indigo→violet, bottom-right, `blobDriftB` (26s)
  - `.login-bg-extra` — violet, center, `blobDriftC` (18s)
- All `@keyframes` animate only `transform` (translate/scale) and `opacity`, with `will-change: transform, opacity`. Long durations, `ease-in-out`, `infinite alternate`. Peak blob opacity stays low (0.10–0.16).
- Added an `@media (prefers-reduced-motion: reduce)` block setting `animation: none` on all three layers — the static gradient backdrop (untouched body `background-image` plus the now-still blobs) remains.
- Left the `<form>`, `csrf_token` hidden input, the Jinja `{% if step %}` toggle, and all input/button styling completely unchanged.

## Verification

Plan automated check passed:
```
@keyframes present, prefers-reduced-motion present, login-bg layer present,
csrf_token retained, 0 <script> tags. File = 213 lines (well under 300-line threshold).
```
- `<form>` / `csrf_token` / step toggle unchanged: confirmed (only the `<style>` block and the new `.login-bg` markup were added; commit diff is +83 insertions, 0 deletions).
- Animated layer is behind the card (z-index 0 vs card z-index 1): confirmed.
- No new dependencies / no `<script>` tags: confirmed.

## Deviations from Plan

None — plan executed as written. The plan suggested keeping the file under ~180 lines; the final file is 213 lines, still comfortably under the project's ~300-line refactor threshold (CLAUDE.md convention). This is a soft target, not a hard constraint, and the extra lines are the three keyframe blocks plus the reduced-motion guard.

## Pending Visual Approval (Checkpoint — NOT blocked here)

Task 2 is a `checkpoint:human-verify` (gate="blocking"). Per the quick-task execution constraints, this autonomous executor does NOT block on visual checkpoints. The operator should verify:

1. `python ghana_cap_app.py`, open http://localhost:5000/login
2. Step 1 (email): subtle, slowly-moving abstract background behind the glass card; "Email Address" field + "Send Verification Code" button fully legible.
3. Submit a seed email (e.g. francis@example.com) → step 2; read the 6-digit code from server stdout (RESEND_API_KEY likely unset). Same backdrop behind the "Verification Code" card; input + "Verify & Login" remain legible.
4. (Optional) Emulate `prefers-reduced-motion: reduce` (OS setting or DevTools → Rendering) and reload — animation stops, static gradient remains.

Resume signal: type "approved", or describe adjustments ("too bright", "too fast", "blobs distracting").

## Known Stubs

None.

## Self-Check: PASSED
- `templates/login.html` exists and contains the animated background: FOUND
- Commit `bbcef86`: FOUND
