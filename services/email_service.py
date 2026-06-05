"""Transactional email service — Resend API for OTP delivery.

Phase 1 contract:
    send_verification_email(receiver_email, code) -> bool

Graceful degradation: without RESEND_API_KEY, the verification code is logged
to stdout and the function still returns True so the login flow proceeds in
dev. This mirrors the prior SMTP behaviour (PRD: "code logged to stdout when
SMTP is unconfigured") so the local dev story is unchanged.
"""
from __future__ import annotations

import logging
import os
import threading

logger = logging.getLogger(__name__)

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "").strip()
RESEND_FROM = os.environ.get(
    "RESEND_FROM",
    "Ghana CAP Platform <onboarding@resend.dev>",
)
# Wall-clock budget for a single Resend HTTP call. The SDK's default is 30s,
# which under eventlet's monkey-patched socket can stretch to minutes if DNS
# or the TLS handshake stalls. A short budget keeps the login flow snappy.
RESEND_TIMEOUT_SEC = int(os.environ.get("RESEND_TIMEOUT_SEC", "8"))

_resend = None
if RESEND_API_KEY:
    try:
        import resend as _resend_mod
        _resend_mod.api_key = RESEND_API_KEY
        # Override the SDK's default 30s requests timeout.
        try:
            from resend.http_client_requests import RequestsClient  # type: ignore
            _resend_mod.default_http_client = RequestsClient(timeout=RESEND_TIMEOUT_SEC)
        except Exception as e:
            logger.warning("Could not pin Resend client timeout (%s). Using SDK default.", e)
        _resend = _resend_mod
        logger.info(
            "Resend email service initialised (from=%s, timeout=%ds).",
            RESEND_FROM, RESEND_TIMEOUT_SEC,
        )
    except Exception as e:
        logger.warning("Resend SDK init failed: %s. Email service will log codes to stdout.", e)
else:
    logger.info("RESEND_API_KEY not set — email service will log codes to stdout.")


def _render_email(code: str) -> tuple[str, str]:
    """Return (html_body, plain_text_body) for the OTP email."""
    html = f"""\
<!DOCTYPE html>
<html>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 24px; color: #0f172a;">
  <div style="max-width: 480px; margin: 0 auto; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 32px;">
    <h1 style="font-size: 20px; margin: 0 0 16px;">Ghana CAP Platform</h1>
    <p style="font-size: 14px; line-height: 1.6; color: #334155; margin: 0 0 16px;">
      Your sign-in verification code is:
    </p>
    <div style="font-family: 'SF Mono', Menlo, Consolas, monospace; font-size: 32px; font-weight: 700; letter-spacing: 6px; padding: 16px; background: #f1f5f9; border-radius: 8px; text-align: center; color: #0f172a;">
      {code}
    </div>
    <p style="font-size: 12px; line-height: 1.6; color: #64748b; margin: 16px 0 0;">
      The code expires in 10 minutes. If you didn't request it, you can safely ignore this email.
    </p>
  </div>
</body>
</html>
"""
    text = (
        f"Ghana CAP Platform\n\n"
        f"Your sign-in verification code: {code}\n\n"
        f"The code expires in 10 minutes. If you didn't request it, ignore this email."
    )
    return html, text


def _send_via_resend(receiver_email: str, code: str) -> None:
    """Background helper: actually call Resend. Logs success or failure but
    never raises (we're inside a daemon thread)."""
    html, text = _render_email(code)
    params = {
        "from": RESEND_FROM,
        "to": [receiver_email],
        "subject": "Ghana CAP Platform — verification code",
        "html": html,
        "text": text,
    }
    try:
        result = _resend.Emails.send(params)
        email_id = result.get("id") if isinstance(result, dict) else getattr(result, "id", None)
        logger.info("Verification email sent to %s via Resend (id=%s).", receiver_email, email_id)
    except Exception as e:
        # Always log the code on failure so the operator can still complete
        # login from the server console — preserves the graceful-degradation
        # invariant when Resend stalls or rejects.
        logger.error("Resend send failed for %s: %s. Code was: %s", receiver_email, e, code)


def send_verification_email(receiver_email: str, code: str) -> bool:
    """Hand the OTP off for delivery. Returns immediately — the actual
    Resend HTTP call runs in a daemon thread so a slow/hanging API call
    never blocks the /login response.

    Returns True on dispatch (queued) OR on configured-fallback (log to
    stdout). Always logs the code as well so the operator can recover from
    a Resend failure without re-requesting a new code.
    """
    if not _resend:
        logger.warning("Email service not configured. Code for %s is %s", receiver_email, code)
        return True  # graceful-degradation: dev / unconfigured envs still log in.

    # Belt-and-braces: log the code locally first so it's recoverable even
    # if Resend stalls or the network drops. The logger.info is guarded by
    # the configured log level — operators running in production at WARN+
    # won't see it, but in dev/staging it's a useful safety net.
    logger.info("Dispatching OTP to %s (code logged for fallback: %s).", receiver_email, code)

    t = threading.Thread(
        target=_send_via_resend, args=(receiver_email, code), daemon=True
    )
    t.start()
    return True
