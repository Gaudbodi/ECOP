---
phase: quick-260605-dzy
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - templates/login.html
autonomous: false
requirements: []

must_haves:
  truths:
    - "The login (step 1, email) page shows a subtle animated background behind the glass card"
    - "The verification-code (step 2) page shows the same animated background"
    - "The form fields and buttons remain fully legible — text contrast is unaffected by the animation"
    - "With prefers-reduced-motion: reduce, the animation is disabled (static gradient remains)"
  artifacts:
    - path: "templates/login.html"
      provides: "Animated glassmorphism background behind the login/verification card"
      contains: "@keyframes"
  key_links:
    - from: "templates/login.html .login-bg layer"
      to: "body / .login-card"
      via: "fixed/absolute element painted behind the card (z-index ordering)"
      pattern: "z-index"
---

<objective>
Add an abstract, subtle, performant animated background to the login and verification-code
pages. The login flow lives entirely in the Flask-served Jinja template
`templates/login.html` (the React SPA redirects to `/login` on 401 — it has no login UI of
its own). Both the email step (step 1) and the code step (step 2) render inside the same
`.login-card`, so a single background layer covers both.

Purpose: Bring the login surface in line with the platform's glassmorphism design language
and make the otherwise-static auth screen feel alive, without harming legibility or
performance.

Output: An updated `templates/login.html` with a pure-CSS animated background layer behind
the glass card.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@./CLAUDE.md
@templates/login.html

<notes>
- The active login surface is the Jinja template `templates/login.html`, served by
  `ghana_cap_app.py` at `@app.route('/login')` (lines 218-271). The React SPA under
  `frontend/` has NO login/OTP component — `frontend/src/api/client.ts:38` does
  `window.location.href = '/login'` on a 401, handing auth back to Flask. Do NOT add a
  login page to the React SPA; this task touches only `templates/login.html`.
- `templates/login.html` is fully self-contained: a single inline `<style>` block, a body
  that flex-centers one `.login-card`, and a Jinja `{% if step == '1' %}` / `{% else %}`
  toggle between the email input and the 6-digit code input — both inside the same card.
- Existing design tokens already in the template's `:root`:
    --bg-color: #0f172a; --accent-color: #38bdf8; --glass-bg: rgba(255,255,255,0.05);
    --glass-border: rgba(255,255,255,0.1);
  The body already paints two static radial gradients (cyan, low-opacity) — the animation
  should build on this same low-saturation cyan/indigo palette, not introduce new bright hues.
- `.login-card` already has `backdrop-filter: blur(12px)`, so any animated layer painted
  behind it is automatically blurred/diffused under the glass — legibility is preserved by
  the existing glass, not by dimming the animation.
- Constraint from `.planning` context: CSS keyframes only — no canvas/requestAnimationFrame
  loops, no new dependencies. (framer-motion/`motion` exists in the React app but NOT in this
  Jinja page, and we are not adding script tags here.)
- Constraint from CLAUDE.md: iterate on the existing pattern; keep the file tidy. This page
  is well under the ~300-line refactor threshold (~130 lines) — keep it that way.
</notes>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add a pure-CSS animated glassmorphism background behind the login card</name>
  <files>templates/login.html</files>
  <action>
Edit only the inline `<style>` block and the `<body>` markup in templates/login.html. Do
NOT touch the `<form>`, the Jinja `{% if step %}` logic, the csrf_token hidden input, or any
input/button styling — those are load-bearing for the auth flow.

1. Add an animated background layer that sits BEHIND the `.login-card`. Implement it as a
   single fixed-position element (e.g. a `<div class="login-bg" aria-hidden="true"></div>`
   placed as the first child of `<body>`), styled with `position: fixed; inset: 0; z-index: 0;
   pointer-events: none;`. Give `.login-card` `position: relative; z-index: 1;` so it always
   paints above the background. Keep the body's existing flex-centering.

2. The animation must be abstract, subtle, and low-saturation, reusing the existing cyan
   (#38bdf8) + indigo (#818cf8 / #8b5cf6) palette already in the file against the #0f172a
   base. Use 2-4 large, soft radial-gradient "blobs" (or aurora bands) that drift/scale slowly
   via @keyframes — long durations (~14-26s), `ease-in-out`, `infinite alternate`. Keep peak
   blob opacity low (roughly 0.10-0.18) so the card stays the focal point. Animate only
   `transform` (translate/scale) and/or `opacity` — never animate `background-position` of a
   blurred element or box-shadow/filter on the blobs (those force expensive repaints). Prefer
   `transform` + `will-change: transform` on the moving layers for GPU compositing.

3. You MAY keep or fold in the body's existing two static radial gradients as the base layer;
   the animated blobs go on top of that base but behind the card.

4. Respect motion preferences: add an
   `@media (prefers-reduced-motion: reduce)` block that sets `animation: none` on the animated
   layers (the static gradient backdrop remains, so the page still looks intentional).

5. Do not add any `<script>` tags, external fonts, or dependencies. Keep everything inline in
   the existing `<style>` block. Keep the total file comfortably under ~180 lines.
  </action>
  <verify>
    <automated>cd "C:\Users\franc\OneDrive\Documents\Mark2.5\EMERGENCY" && python -c "import re; s=open('templates/login.html',encoding='utf-8').read(); assert '@keyframes' in s, 'no keyframes added'; assert 'prefers-reduced-motion' in s, 'no reduced-motion guard'; assert 'login-bg' in s or 'aurora' in s, 'no dedicated background layer'; assert 'csrf_token' in s, 'csrf token must remain'; assert s.count('<script') == 0, 'no script tags allowed'; print('OK')"</automated>
  </verify>
  <done>
templates/login.html contains at least one @keyframes animation driving a background layer
that paints behind `.login-card`, a `prefers-reduced-motion: reduce` guard disabling it, no
`<script>` tags, and an unchanged form (csrf_token + step toggle intact). The page renders
with the card clearly legible above a subtly moving low-saturation cyan/indigo backdrop.
  </done>
</task>

<task type="checkpoint:human-verify" gate="blocking">
  <what-built>A pure-CSS animated glassmorphism background behind the login + verification-code card in templates/login.html.</what-built>
  <how-to-verify>
1. Start the app: `python ghana_cap_app.py`
2. Open http://localhost:5000/login
3. Confirm the email-step (step 1) page shows a subtle, slowly-moving abstract background
   behind the glass card, and the "Email Address" field + "Send Verification Code" button
   are fully legible.
4. Submit any seed email (e.g. francis@example.com) to reach the code step (step 2); read the
   6-digit code from the server log (RESEND_API_KEY likely unset, so it prints to stdout).
   Confirm the same animated background shows behind the "Verification Code" card and the
   input + "Verify & Login" button remain legible.
5. (Optional) Enable OS "reduce motion" (or DevTools → Rendering → Emulate
   prefers-reduced-motion: reduce) and reload /login — the animation should stop while the
   static gradient backdrop remains.
  </how-to-verify>
  <resume-signal>Type "approved" or describe what to adjust (e.g. "too bright", "too fast", "blobs distracting").</resume-signal>
</task>

</tasks>

<verification>
- `templates/login.html` contains `@keyframes` and a `prefers-reduced-motion: reduce` block.
- The `<form>`, `csrf_token` hidden input, and Jinja `{% if step %}` toggle are unchanged.
- No `<script>` tags were added; no new dependencies introduced.
- The animated layer sits behind `.login-card` (lower z-index); the card stays the focal point.
</verification>

<success_criteria>
- Both login steps (email + verification code) display a subtle animated background matching
  the existing glassmorphism cyan/indigo palette.
- Form fields and buttons remain fully legible.
- Animation is pure CSS (no canvas loops, no new dependencies) and honors
  prefers-reduced-motion.
- Operator approves the visual result at the human-verify checkpoint.
</success_criteria>

<output>
After completion, create `.planning/quick/260605-dzy-add-abstract-animated-background-to-logi/260605-dzy-SUMMARY.md`
</output>
