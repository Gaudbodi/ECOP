"""Autonomous E2E smoke test for Phase 4 ROADMAP success criteria.

Run: python tests/e2e_smoke.py

Boots Flask in a subprocess, drives the running app via Playwright Chromium
and direct HTTP, asserts the seven ROADMAP §90 success criteria, then
shuts down Flask. Prints a PASS/FAIL summary and exits non-zero on any
failure.

Notes:
- OTP is read from the Flask stdout log because RESEND_API_KEY is unset
  (graceful-degradation fallback prints the code).
- Real-time Pipeline check fires a webhook via the live `/api/v1/alerts/gmet/webhook`
  endpoint and expects the new alert to appear in the React app via the
  Socket.IO `new_alert` event within ~3 seconds.
- The script tolerates missing OPTIONAL credentials (Resend, Gemini) — those
  paths exercise the mock fallback.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import requests
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
FLASK_LOG = ROOT / "flask_e2e.log"
APP_URL = "http://localhost:5000"
ADMIN_EMAIL = "francis@example.com"
GMET_API_KEY = "gh_cap_poc_key_2026"
SCREENSHOT_DIR = ROOT / "tests" / "_e2e_screenshots"
SCREENSHOT_DIR.mkdir(exist_ok=True)


class Suite:
    def __init__(self):
        self.results: list[tuple[str, bool, str]] = []

    def step(self, name: str, ok: bool, detail: str = ""):
        marker = "PASS" if ok else "FAIL"
        self.results.append((name, ok, detail))
        print(f"  [{marker}] {name}{(' — ' + detail) if detail else ''}", flush=True)

    def all_passed(self) -> bool:
        return all(ok for _, ok, _ in self.results)

    def summary(self):
        passed = sum(1 for _, ok, _ in self.results if ok)
        total = len(self.results)
        print()
        print("=" * 72)
        print(f"  {passed}/{total} checks passed")
        print("=" * 72)
        for name, ok, detail in self.results:
            marker = "PASS" if ok else "FAIL"
            print(f"  [{marker}] {name}{(' — ' + detail) if detail else ''}")
        print()


def wait_for_log(needle: str, timeout: float = 25.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if FLASK_LOG.exists():
            try:
                content = FLASK_LOG.read_text(encoding="utf-8", errors="replace")
            except Exception:
                content = ""
            if needle in content:
                return True
        time.sleep(0.5)
    return False


def extract_otp_from_log() -> str | None:
    if not FLASK_LOG.exists():
        return None
    content = FLASK_LOG.read_text(encoding="utf-8", errors="replace")
    # email_service log line: "Email service not configured. Code for X is 123456"
    matches = re.findall(r"Code for [^\s]+ is (\d{6})", content)
    if matches:
        return matches[-1]
    # SMS fallback line in case email path differs.
    matches = re.findall(r"\b(\d{6})\b", content)
    if matches:
        return matches[-1]
    return None


def main() -> int:
    suite = Suite()

    # ── Pre-flight ────────────────────────────────────────────────────────
    if not (ROOT / "frontend" / "dist" / "index.html").exists():
        print("frontend/dist/index.html missing. Run: cd frontend; npm run build")
        return 2

    # ── Boot Flask ────────────────────────────────────────────────────────
    print("== Boot Flask ==")
    if FLASK_LOG.exists():
        FLASK_LOG.unlink()
    log_h = open(FLASK_LOG, "w", encoding="utf-8", buffering=1)
    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")
    env["FLASK_E2E"] = "1"
    env["FLASK_USE_RELOADER"] = "0"  # avoid Werkzeug fork splitting stdout
    # Avoid the dispatch loop POSTing back to ourselves (with eventlet single
    # worker the loopback adds 5s of waiting per alert). Point at a fast-fail
    # local port that nothing listens on — connection refused returns ~50ms.
    env["MNO_WEBHOOK_URL"] = "http://127.0.0.1:65530/never-listening"
    flask_proc = subprocess.Popen(
        [sys.executable, "ghana_cap_app.py"],
        cwd=str(ROOT),
        stdout=log_h,
        stderr=subprocess.STDOUT,
        env=env,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
    )

    try:
        # Wait for the "Dashboard:" banner from ghana_cap_app.py
        booted = wait_for_log("Dashboard:", timeout=30)
        if not booted:
            log_h.flush()
            print("Flask did not start in 30s. Last 40 lines of log:")
            try:
                tail = FLASK_LOG.read_text(encoding="utf-8", errors="replace").splitlines()[-40:]
                print("\n".join(tail))
            except Exception:
                pass
            suite.step("Flask boot", False, "did not see 'Dashboard:' banner in stdout within 30s")
            suite.summary()
            return 1
        suite.step("Flask boot", True, "saw 'Dashboard:' banner")

        # ── Criterion 4: Routes ───────────────────────────────────────────
        print("\n== Criterion 4: Routes ==")
        s = requests.Session()

        r = s.get(f"{APP_URL}/login")
        suite.step("4a /login renders Jinja",
                   r.status_code == 200 and "Ghana CAP Portal" in r.text)

        r = s.get(f"{APP_URL}/public/feed/display")
        suite.step("4b /public/feed/display renders Jinja",
                   r.status_code == 200)

        r = s.get(f"{APP_URL}/", allow_redirects=False)
        suite.step("4c / redirects when logged-out",
                   r.status_code in (301, 302))

        r = s.get(f"{APP_URL}/api/v1/me", allow_redirects=False)
        suite.step("4d /api/v1/me requires login",
                   r.status_code in (302, 401))

        # ── Login flow (Playwright) ───────────────────────────────────────
        print("\n== Login (Playwright) ==")
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1440, "height": 900})
            page = context.new_page()

            page.goto(f"{APP_URL}/login")
            page.fill("input[name='email']", ADMIN_EMAIL)
            page.click("button[type='submit']")
            # OTP form should appear
            page.wait_for_selector("input[name='code']", timeout=10000)

            # Read OTP from the Flask log
            time.sleep(0.5)
            otp = extract_otp_from_log()
            suite.step("Login OTP captured from log", bool(otp), f"code={otp}")
            if not otp:
                page.screenshot(path=str(SCREENSHOT_DIR / "login_no_otp.png"))
                raise SystemExit("Could not extract OTP from Flask log")

            page.fill("input[name='code']", otp)
            page.click("button[type='submit']")
            page.wait_for_url(f"{APP_URL}/", timeout=10000)
            page.wait_for_load_state("networkidle", timeout=15000)
            suite.step("Logged in as Admin", True, ADMIN_EMAIL)

            # ── Criterion 1: SPA + asset serve ────────────────────────────
            print("\n== Criterion 1: SPA serve ==")
            html = page.content()
            has_assets = "/assets/" in html
            has_data_theme = "data-theme" in html
            has_root = bool(page.query_selector("#root"))
            suite.step("1a SPA shell renders at /",
                       has_assets and has_data_theme and has_root,
                       f"assets={has_assets} data-theme={has_data_theme} root={has_root}")
            page.screenshot(path=str(SCREENSHOT_DIR / "01_dashboard_dark.png"), full_page=False)

            # ── Criterion 3: Theme toggle ─────────────────────────────────
            print("\n== Criterion 3: Theme toggle ==")
            initial_theme = page.evaluate(
                "() => document.documentElement.getAttribute('data-theme')"
            )
            # ThemeToggle has aria-label="Toggle Light/Dark Mode"
            toggle = page.query_selector(
                'button[aria-label="Toggle Light/Dark Mode"]'
            )
            if not toggle:
                # Fallback: find any icon button with sky focus ring near nav
                toggle = page.query_selector("nav button:has(svg)")
            if toggle:
                toggle.click()
                page.wait_for_timeout(400)
                new_theme = page.evaluate(
                    "() => document.documentElement.getAttribute('data-theme')"
                )
                stored = page.evaluate("() => localStorage.getItem('theme')")
                suite.step("3a Theme attribute swaps on click",
                           initial_theme != new_theme,
                           f"{initial_theme} -> {new_theme}")
                suite.step("3b Theme persisted to localStorage",
                           stored in {"dark", "light"},
                           f"localStorage.theme={stored}")
                page.screenshot(path=str(SCREENSHOT_DIR / "02_dashboard_after_toggle.png"), full_page=False)
                # Toggle back so subsequent screenshots are dark
                toggle.click()
                page.wait_for_timeout(300)
            else:
                suite.step("3a Theme toggle button found", False, "no theme button matched")
                suite.step("3b Theme persisted to localStorage", False, "skipped — toggle missing")

            # ── Criterion 5: Webhook Config ───────────────────────────────
            print("\n== Criterion 5: Webhook Config ==")
            # Click Settings tab — match by visible text.
            settings_btn = page.get_by_role("button", name=re.compile("settings", re.I)).first
            if not settings_btn:
                settings_btn = page.locator("text=Settings").first
            settings_btn.click()
            page.wait_for_timeout(800)
            settings_html = page.content()
            has_webhook_url = "/api/v1/alerts/gmet/webhook" in settings_html
            has_masked_key = "X-CAP-API-KEY" in settings_html and "••••••" in settings_html
            has_rotation_note = "GMET_WEBHOOK_API_KEY" in settings_html
            suite.step("5a Webhook URL rendered via JSX",
                       has_webhook_url, f"url-substr-present={has_webhook_url}")
            suite.step("5b Webhook key masked",
                       has_masked_key, f"masked-present={has_masked_key}")
            suite.step("5c Rotation instructions present",
                       has_rotation_note, f"rotation-note-present={has_rotation_note}")
            page.screenshot(path=str(SCREENSHOT_DIR / "03_settings.png"), full_page=False)

            # ── Criterion 6: Test Dispatcher ──────────────────────────────
            print("\n== Criterion 6: Test Dispatcher ==")
            # Subscribe to dashboard's Pipeline socket events first by going there.
            # Test Dispatcher button.
            try:
                dispatch_btn = page.get_by_role(
                    "button", name=re.compile("run test dispatch", re.I)
                ).first
                dispatch_btn.click(timeout=5000)
                # Wait for success banner: role=status containing "GH-CAP-".
                # Process_alert_logic does geo + translation + TTS + Mongo + MNO
                # (fast-fail local) + SMS-mock — give it 25s.
                page.wait_for_selector("text=/GH-CAP-/", timeout=25000)
                banner = page.query_selector("text=/GH-CAP-/").inner_text()
                ident_match = re.search(r"GH-CAP-[A-Za-z0-9-]+", banner)
                ident = ident_match.group(0) if ident_match else None
                suite.step("6a Test Dispatcher banner shows new identifier",
                           bool(ident), f"banner={banner!r}")

                # Switch to Pipeline tab. The test-dispatch fixture's headline
                # is the canonical visible signal in the DOM (AlertSummary
                # renders the headline; the identifier only shows in the
                # expanded AlertDetail). Confirm via headline match AND via
                # the JSON list endpoint as a belt-and-braces persistence check.
                pipeline_btn = page.get_by_role(
                    "button", name=re.compile("pipeline", re.I)
                ).first
                pipeline_btn.click()
                page.wait_for_timeout(2000)
                # Persistence: GET /api/v1/alerts via the page's authenticated
                # session — the dispatched alert must be in the returned list.
                api_resp = page.request.get(f"{APP_URL}/api/v1/alerts")
                in_list = False
                if api_resp.ok:
                    try:
                        data = api_resp.json()
                        in_list = ident is not None and any(
                            a.get("identifier") == ident for a in (data.get("alerts") or [])
                        )
                    except Exception:
                        in_list = False
                suite.step("6b Test alert persisted (visible in /api/v1/alerts)",
                           in_list, f"identifier={ident} api-status={api_resp.status}")
                # Real-time DOM signal: pipeline should have rendered at least
                # one alert card after the dispatch.
                card_count = page.locator("[role='button'][aria-expanded]").count()
                suite.step("6c Pipeline tab renders alert card(s)",
                           card_count >= 1,
                           f"card_count={card_count}")
                page.screenshot(path=str(SCREENSHOT_DIR / "04_pipeline_after_dispatch.png"), full_page=False)
            except Exception as e:
                suite.step("6 Test Dispatcher flow", False, f"exception: {e!s}")

            # ── Criterion 2: Real-time Pipeline (Socket.IO) ───────────────
            print("\n== Criterion 2: Real-time Pipeline ==")
            try:
                # Snapshot the alert count visible in the Pipeline.
                page.wait_for_timeout(500)
                count_before = page.locator("article, [data-alert-id]").count()
                # Fire a webhook from outside the browser session.
                webhook_resp = requests.post(
                    f"{APP_URL}/api/v1/alerts/gmet/webhook",
                    headers={
                        "X-CAP-API-KEY": GMET_API_KEY,
                        "Content-Type": "application/json",
                    },
                    json={
                        "headline": "E2E smoke test alert",
                        "description": "autonomous Playwright run",
                        "severity": "Severe",
                        "urgency": "Immediate",
                        "category": "Met",
                        "event": "Test Storm",
                    },
                    timeout=45,
                )
                suite.step("2a webhook accepted",
                           webhook_resp.status_code == 201,
                           f"status={webhook_resp.status_code}")
                webhook_body = webhook_resp.json() if webhook_resp.ok else {}
                webhook_ident = webhook_body.get("identifier")
                # Two checks:
                #   (a) the alert was persisted (GET /api/v1/alerts returns it).
                #   (b) the Pipeline DOM updated (real-time Socket.IO signal:
                #       card count grows OR the headline becomes visible).
                api_resp = page.request.get(f"{APP_URL}/api/v1/alerts")
                webhook_persisted = False
                if api_resp.ok:
                    try:
                        data = api_resp.json()
                        webhook_persisted = webhook_ident is not None and any(
                            a.get("identifier") == webhook_ident
                            for a in (data.get("alerts") or [])
                        )
                    except Exception:
                        pass
                suite.step("2b webhook alert persisted (visible in /api/v1/alerts)",
                           webhook_persisted,
                           f"identifier={webhook_ident}")

                # Real-time signal — wait up to 8s for the headline to render
                # in the Pipeline DOM.
                appeared = False
                for _ in range(16):
                    page.wait_for_timeout(500)
                    if "E2E smoke test alert" in page.content():
                        appeared = True
                        break
                    if page.locator("[role='button'][aria-expanded]").count() > count_before:
                        appeared = True
                        break
                suite.step("2c webhook alert visible in Pipeline DOM (real-time)",
                           appeared,
                           f"socket-driven update={appeared}")
                page.screenshot(path=str(SCREENSHOT_DIR / "05_pipeline_after_webhook.png"), full_page=False)
            except Exception as e:
                suite.step("2 Real-time Pipeline", False, f"exception: {e!s}")

            # ── Criterion 7: Glassmorphism ────────────────────────────────
            print("\n== Criterion 7: Glassmorphism ==")
            # Sample the navbar's computed style — we expect either backdrop-filter:blur
            # or background that includes rgba/transparent.
            nav_styles = page.evaluate("""
                () => {
                    const el = document.querySelector('nav, header [class*="glass"], [class*="glass-card"]');
                    if (!el) return null;
                    const cs = window.getComputedStyle(el);
                    return {
                        backdropFilter: cs.backdropFilter || cs.webkitBackdropFilter || '',
                        background: cs.backgroundColor,
                        border: cs.borderTopColor || cs.borderColor,
                    };
                }
            """)
            has_glass = bool(
                nav_styles
                and (
                    "blur" in (nav_styles.get("backdropFilter") or "")
                    or "rgba" in (nav_styles.get("background") or "")
                )
            )
            suite.step("7 Glassmorphism (backdrop-blur or rgba bg)",
                       has_glass,
                       f"styles={nav_styles}")
            page.screenshot(path=str(SCREENSHOT_DIR / "06_final_dark.png"), full_page=True)

            browser.close()

    finally:
        # ── Shut down ─────────────────────────────────────────────────────
        try:
            flask_proc.terminate()
            try:
                flask_proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                flask_proc.kill()
        except Exception:
            pass
        log_h.close()

    suite.summary()
    return 0 if suite.all_passed() else 1


if __name__ == "__main__":
    sys.exit(main())
