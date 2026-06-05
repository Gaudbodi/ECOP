import os
import uuid
import secrets
import logging

# Phase 3: load .env BEFORE any os.environ reads. Fails silently if dotenv
# is unavailable so we don't block boot in container envs that already inject
# vars directly.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Phase 3: detect the known-malformed OPENAI_API_KEY pattern that the user's
# .env historically carried (`OpenAI(api_key="sk-…")` instead of a bare key).
# Treat malformed values as missing so enrichment_service falls back to the
# mock path cleanly with a single, loud warning instead of a confusing OpenAI
# auth error.
_raw_openai = os.environ.get("OPENAI_API_KEY", "").strip()
if _raw_openai and ("OpenAI(api_key" in _raw_openai or _raw_openai.startswith("OpenAI(")):
    logging.warning(
        "OPENAI_API_KEY in .env is malformed (looks like a Python expression). "
        "Set OPENAI_API_KEY to the bare key string (sk-...) — using mock fallbacks until fixed."
    )
    os.environ["OPENAI_API_KEY"] = ""

from datetime import datetime, timezone
from functools import wraps
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
from flask_socketio import SocketIO, emit
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import check_password_hash

# Import local modules
from db import (
    save_alert,
    get_all_alerts,
    find_alert_by_identifier,
    seed_users,
    get_user_by_staff_id,
    get_user_by_email,
    save_verification_code,
    verify_code,
    is_email_locked,
    update_alert_workflow,
    list_users,
    create_user,
)
from services.geo_service import geo_service
from services.enrichment_service import enrichment_service
from services.dispatch_service import dispatch_service
from services.email_service import send_verification_email
from services.sms_2fa_service import sms_2fa_service
from services.external_analytics_service import external_analytics_service
from services.advisory_agent_service import advisory_agent_service

# Logging configuration — force=True overrides any handler that eventlet /
# flask configured earlier; without it our service-level INFO logs are
# silently dropped and operators only see werkzeug request lines.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True,
)

# Phase 1 hygiene: read secrets from env with a fallback to the current literal to
# preserve active sessions and the GMeT webhook contract during migration. Phase 2
# follow-up will rotate these values and remove the fallback (raise on missing).
_DEFAULT_SECRET_KEY = 'ghana_cap_secret_secure_2026!'
_DEFAULT_GMET_WEBHOOK_API_KEY = 'gh_cap_poc_key_2026'

_env_secret_key = os.environ.get('FLASK_SECRET_KEY')
_env_gmet_key = os.environ.get('GMET_WEBHOOK_API_KEY')
SECRET_KEY = _env_secret_key or _DEFAULT_SECRET_KEY
GMET_WEBHOOK_API_KEY = _env_gmet_key or _DEFAULT_GMET_WEBHOOK_API_KEY

# Warn only when the env var was missing/blank — not when it happens to
# match the compiled-in fallback value. (The user's .env intentionally
# pins the key to the same value as the fallback to keep the GMeT
# contract stable, and a spurious warning every boot is noise.)
if not _env_secret_key:
    logging.warning("FLASK_SECRET_KEY not set in env — using compiled-in fallback. Rotate in Phase 2.")
if not _env_gmet_key:
    logging.warning("GMET_WEBHOOK_API_KEY not set in env — using compiled-in fallback. Rotate in Phase 2.")

# Phase 2: lock down CORS to known origins (default = local dev). Comma-separated.
_default_origins = "http://localhost:5000,http://127.0.0.1:5000,http://localhost:5173"
ALLOWED_ORIGINS = [o.strip() for o in os.environ.get('ALLOWED_ORIGINS', _default_origins).split(',') if o.strip()]

# Render injects RENDER_EXTERNAL_URL (e.g. https://ghana-cap-platform.onrender.com)
# with the service's own public URL. Trust it for Socket.IO CORS so same-origin
# WebSocket upgrades from the deployed SPA aren't rejected — avoids hardcoding the
# live hostname (which isn't known until the service is first created).
_render_external_url = os.environ.get('RENDER_EXTERNAL_URL', '').strip().rstrip('/')
if _render_external_url and _render_external_url not in ALLOWED_ORIGINS:
    ALLOWED_ORIGINS.append(_render_external_url)
    logging.info("Added RENDER_EXTERNAL_URL to allowed origins: %s", _render_external_url)

# Phase 2: Secure cookies in prod; relaxed in dev so HTTP login still works.
_is_production = os.environ.get('FLASK_ENV', '').lower() == 'production'

# Phase 4: Vite build output. Resolved relative to this file so it works under
# both `python ghana_cap_app.py` (cwd = repo root) and `gunicorn ghana_cap_app:app`
# (cwd may differ). RESEARCH.md Pitfall #8.
FRONTEND_DIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend', 'dist')

app = Flask(__name__)
app.config.update(
    SECRET_KEY=SECRET_KEY,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=_is_production,
    PERMANENT_SESSION_LIFETIME=3600,  # 1h
    # WTF-CSRF settings
    WTF_CSRF_TIME_LIMIT=3600,
)

socketio = SocketIO(app, cors_allowed_origins=ALLOWED_ORIGINS)

# Phase 2: CSRF on form-based routes; JSON endpoints are exempted explicitly
# below (Phase 4 frontend migration will add token-in-header handling).
csrf = CSRFProtect(app)

# Phase 2: per-IP rate limiting (defaults conservative; per-route stricter
# limits applied via @limiter.limit on /login).
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["200 per hour"],
    storage_uri="memory://",  # PoC: in-memory; prod should swap for redis
)

# Seed users on startup
seed_users()

# --- Auth Decorators ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def check_ip_restriction(user, client_ip):
    allowed = user.get('allowed_ips', [])
    if "*" in allowed:
        return True
    return client_ip in allowed


def super_admin_required(f):
    """Authorisation gate for the user-onboarding admin panel. The Super Admin
    role is the *only* role allowed to create, list, or remove other operator
    accounts. Regular Admins manage alerts but cannot mint new users."""
    @wraps(f)
    def decorated(*args, **kwargs):
        u = session.get('user') or {}
        if u.get('role') != 'Super Admin':
            return jsonify({"error": "forbidden", "detail": "Super Admin role required."}), 403
        return f(*args, **kwargs)
    return decorated


# Catalog of emergency-services stakeholder agencies the Super Admin can
# attach a new user to. Order is by operational prominence in Ghana's
# disaster-response stack, not alphabetical.
EMERGENCY_STAKEHOLDERS = [
    {"id": "NADMO", "name": "National Disaster Management Organisation",
     "scope": "Coordination", "color": "#f97316"},
    {"id": "GMeT",  "name": "Ghana Meteorological Agency",
     "scope": "Weather alerts (origin)", "color": "#0ea5e9"},
    {"id": "GPS",   "name": "Ghana Police Service",
     "scope": "Public safety + traffic", "color": "#1d4ed8"},
    {"id": "GFRS",  "name": "Ghana National Fire Service",
     "scope": "Fire + rescue", "color": "#dc2626"},
    {"id": "GHS",   "name": "Ghana Health Service",
     "scope": "Public health", "color": "#10b981"},
    {"id": "NAS",   "name": "National Ambulance Service",
     "scope": "Pre-hospital emergency", "color": "#22c55e"},
    {"id": "GAF",   "name": "Ghana Armed Forces",
     "scope": "Disaster relief support", "color": "#0f766e"},
    {"id": "EPA",   "name": "Environmental Protection Agency",
     "scope": "Hazard advisories", "color": "#65a30d"},
    {"id": "GRCS",  "name": "Ghana Red Cross Society",
     "scope": "Civil protection / aid", "color": "#ef4444"},
    {"id": "NCA",   "name": "National Communications Authority",
     "scope": "Telecom + public dispatch", "color": "#8b5cf6"},
]
_STAKEHOLDER_IDS = {s["id"] for s in EMERGENCY_STAKEHOLDERS}

# --- Routes ---
def _generate_verification_code():
    """Phase 2: cryptographically secure 6-digit verification code."""
    return f"{secrets.randbelow(900000) + 100000}"


def _send_verification(user, code):
    """Send the verification code via SMS (Africa's Talking → Twilio →
    log-only). Falls back to email if the user has no phone number.

    Email delivery target: prefer `notify_email` when present (lets a user
    log in with a corporate alias while OTPs still land in their actual
    inbox — necessary while Resend's `onboarding@resend.dev` sandbox
    sender only delivers to the account-owner address)."""
    phone = (user or {}).get('phone_number')
    if phone:
        return sms_2fa_service.send_code(phone, code)
    target = (user or {}).get('notify_email') or user['email']
    if target != user['email']:
        logging.info("OTP for %s routed to notify_email %s.", user['email'], target)
    return send_verification_email(target, code)


@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute; 20 per hour", methods=['POST'])
def login():
    if request.method == 'POST':
        email = (request.form.get('email') or '').strip().lower()
        step = request.form.get('step', '1')

        # Generic error to avoid email enumeration / lockout disclosure.
        generic_err = "We couldn't process that request. Please try again later."

        if step == '1':
            if not email:
                return render_template('login.html', error=generic_err)
            if is_email_locked(email):
                logging.warning("Login step 1 denied: email %s is locked.", email)
                return render_template('login.html', error=generic_err)

            user = get_user_by_email(email)
            if user:
                code = _generate_verification_code()
                if save_verification_code(email, code) and _send_verification(user, code):
                    return render_template('login.html', email=email, step='2')

            # Same-shape response for unknown emails to mitigate enumeration —
            # show the code-entry screen even if no code was actually sent.
            return render_template('login.html', email=email, step='2')

        elif step == '2':
            code = (request.form.get('code') or '').strip()
            if not (email and code):
                return render_template('login.html', email=email, step='2', error=generic_err)

            if verify_code(email, code):
                user = get_user_by_email(email)
                if not user:
                    return render_template('login.html', error=generic_err)
                client_ip = request.remote_addr
                if check_ip_restriction(user, client_ip):
                    session['user'] = {
                        "staff_id": user['staff_id'],
                        "name": user['name'],
                        "agency": user['agency'],
                        "role": user['role'],
                        "email": user['email']
                    }
                    session.permanent = True
                    logging.info(f"User {user['name']} logged in from {client_ip}")
                    return redirect(url_for('dashboard'))
                logging.warning("Login denied for %s from disallowed IP %s.", email, client_ip)
                return render_template('login.html', error=generic_err)

            return render_template('login.html', email=email, step='2', error="Invalid or expired verification code.")

    return render_template('login.html', step='1')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    """Phase 4: serve the React SPA shell. The SPA fetches user + alerts via
    GET /api/v1/me and GET /api/v1/alerts on mount."""
    return send_from_directory(FRONTEND_DIST, 'index.html')


@app.route('/assets/<path:filename>')
def frontend_assets(filename):
    """Phase 4: serve hashed Vite build assets (index-*.js, index-*.css, etc.).
    Public — no login_required, matches normal CDN/static-asset semantics."""
    return send_from_directory(os.path.join(FRONTEND_DIST, 'assets'), filename)


@app.route('/api/v1/me', methods=['GET'])
@csrf.exempt  # GET, no state change — CSRF doesn't apply, but keep the decorator pattern visible.
@login_required
def me():
    """Phase 4: returns the current session user for the React navbar +
    role-gating. Mirrors session['user'] shape (ghana_cap_app.py:179-185)."""
    return jsonify(session['user']), 200


@app.route('/api/v1/alerts', methods=['GET'])
@csrf.exempt
@login_required
def list_alerts():
    """Phase 4: JSON alert list for the SPA's Pipeline tab. Mirrors what the
    pre-Phase-4 Jinja dashboard rendered server-side. Graceful-degradation:
    Mongo failure returns 200 + degraded:true so the SPA can render an empty
    state instead of a 500 page (CLAUDE.md invariant)."""
    try:
        raw = get_all_alerts() or []
        # Stringify _id to make it JSON-serializable (RESEARCH.md Pitfall #3).
        # Same pattern as ghana_cap_app.py:278-280 used in validate_alert.
        for a in raw:
            if '_id' in a:
                a['_id'] = str(a['_id'])
        return jsonify({"alerts": raw, "degraded": False}), 200
    except Exception as e:
        logging.error("list_alerts: Mongo read failed: %s", e)
        return jsonify({"alerts": [], "degraded": True, "error": "Datastore unavailable"}), 200


# Phase 4: Test Dispatcher mock payload. Server-side fixture so the React
# button doesn't need to know the canonical GMeT shape, and the API key
# stays out of the browser (RESEARCH.md A7).
_TEST_DISPATCHER_MOCK_PAYLOAD = {
    "headline": "TEST DISPATCH: Heavy Rain Expected at Osu",
    "description": "Synthetic GMeT payload injected via Test Dispatcher button. Heavy rainfall over Greater Accra in the next 6 hours.",
    "instruction": "This is a test alert. Monitor official channels for real warnings.",
    "event": "Rain",
    "category": "Met",
    "severity": "Severe",
    "urgency": "Immediate",
    "certainty": "Likely",
    "status": "Test",
    "msgType": "Alert",
    "scope": "Public",
    "latitude": 5.5567,
    "longitude": -0.1820,
}


@app.route('/api/v1/dispatcher/test', methods=['POST'])
@csrf.exempt
@login_required
def dispatcher_test():
    """Phase 4: Test Dispatcher endpoint. Admin-only. Injects the mock GMeT
    payload through `process_alert_logic` at workflow_stage=3 so it traces
    the dispatch path end-to-end and surfaces in Pipeline via Socket.IO
    `new_alert`. Server-side proxy keeps the GMeT API key out of the browser
    (RESEARCH.md A7)."""
    if session['user'].get('role') != 'Admin':
        return jsonify({"error": "Unauthorized"}), 403

    return process_alert_logic(
        dict(_TEST_DISPATCHER_MOCK_PAYLOAD),  # copy so callers can't mutate the fixture
        sender_info={
            "staff_id": "TEST-DISPATCHER",
            "name": f"Test Dispatcher ({session['user']['name']})",
            "agency": "GMeT",
            "role": "Admin",
        },
        client_ip=request.remote_addr,
        workflow_stage=3,
    )

@app.route('/api/v1/alerts/gmet/webhook', methods=['POST'])
@csrf.exempt  # API-key authed; not a form submission
def gmet_webhook():
    """GMeT Webhook Receiver Endpoint (API Key protected, auto-dispatch)."""
    api_key = request.headers.get('X-CAP-API-KEY')
    if api_key != GMET_WEBHOOK_API_KEY:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    # PRD §6 acceptance #5: GMeT webhook → MNO dispatch within 5 seconds, no human-in-the-loop.
    return process_alert_logic(
        data,
        sender_info={"staff_id": "GMeT-SYSTEM", "name": "GMeT Webhook", "agency": "GMeT"},
        client_ip=request.remote_addr,
        workflow_stage=3,
    )

@app.route('/api/v1/alerts/manual', methods=['POST'])
@csrf.exempt  # JSON endpoint; Phase 4 frontend will move to token-in-header
@login_required
def manual_alert():
    """Manual CAP generation from form"""
    data = request.json
    # Four-place role/stage matrix sync point #1 (CLAUDE.md): only cap generator,
    # Admin, and Super Admin may create alerts. cap validator is denied 403 here.
    # Keep in sync with: validate_alert allowlist (L409), _LIFECYCLE_ROLES (L465),
    # and process_alert_logic dispatch gate (workflow_stage == 3).
    if session['user'].get('role') not in ('cap generator', 'Admin', 'Super Admin'):
        return jsonify({"error": "Unauthorized"}), 403
    sender_info = {
        "staff_id": session['user']['staff_id'],
        "name": session['user']['name'],
        "agency": session['user']['agency'],
        "role": session['user']['role']
    }

    # Generators submit for validation (stage 1); Admin/Super Admin direct-dispatch (stage 3).
    # The else branch only ever sees Admin/Super Admin once validators are blocked above.
    workflow_stage = 1 if sender_info['role'] == 'cap generator' else 3

    return process_alert_logic(data, sender_info=sender_info, client_ip=request.remote_addr, workflow_stage=workflow_stage)

@app.route('/api/v1/alerts/validate/<identifier>', methods=['POST'])
@csrf.exempt  # JSON endpoint; Phase 4 frontend will move to token-in-header
@login_required
def validate_alert(identifier):
    """Validator approves or rejects an alert"""
    if session['user']['role'] not in ['cap validator', 'Admin']:
        return jsonify({"error": "Unauthorized"}), 403
        
    data = request.json
    action = data.get('action') # 'approve' or 'reject'
    
    if action == 'approve':
        alert = find_alert_by_identifier(identifier)
        if not alert:
            return jsonify({"error": "Alert not found"}), 404
            
        if alert.get('workflow_stage') != 1:
            return jsonify({"error": "Alert not in pending state"}), 400
            
        # Dispatch it
        alert['mno_dispatched'] = dispatch_service.dispatch_to_mno(alert)
        sms_text = f"ALERT: {alert['headline']}\n{alert['translations'].get('English', alert['description'])}"
        recipients = ["+233540000000"] # Mock recipients
        alert['sms_sent'] = dispatch_service.send_sms(sms_text, recipients)
        
        # Update stage to 3 (Dispatched)
        update_alert_workflow(identifier, 3, {
            "mno_dispatched": alert['mno_dispatched'],
            "sms_sent": alert['sms_sent'],
            "validated_by": session['user']['name'],
            "validated_at": datetime.now(timezone.utc).isoformat()
        })
        
        # Convert ObjectId to string for JSON serialization
        if '_id' in alert:
            alert['_id'] = str(alert['_id'])
            
        # Notify via socket
        socketio.emit('alert_updated', alert)
        
        # Sync to external analytics
        external_analytics_service.sync_alert(alert)
        
        return jsonify({"status": "success", "message": "Alert approved and dispatched"}), 200
        
    elif action == 'reject':
        update_alert_workflow(identifier, 0, { # 0 for Rejected/Draft
            "rejected_by": session['user']['name'],
            "rejected_reason": data.get('reason', 'No reason provided')
        })
        return jsonify({"status": "success", "message": "Alert rejected"}), 200
        
    return jsonify({"error": "Invalid action"}), 400


# ─── Alert lifecycle (terminate + extend) ──────────────────────────────────
# CAP v1.2 semantics: a "Cancel" message ends an alert, an "Update"
# replaces / amends one. We model both inline on the alert document for UI
# simplicity (the canonical CAP message chain can be reconstructed from the
# lifecycle_history audit trail).

_LIFECYCLE_ROLES = {"cap validator", "Admin", "Super Admin"}


def _broadcast_alert_update(alert):
    """Stringify _id, emit alert_updated, push to public feed."""
    if '_id' in alert:
        alert['_id'] = str(alert['_id'])
    socketio.emit('alert_updated', alert)
    # Mirror the dispatched payload to the public feed so any TV display /
    # subscriber sees the lifecycle change in real time.
    try:
        global _latest_public_alert
        _latest_public_alert = alert
        socketio.emit('alert', alert, namespace='/live_feed')
    except Exception as e:
        logging.warning("Public-feed broadcast failed for %s: %s", alert.get('identifier'), e)


@app.route('/api/v1/alerts/<identifier>/terminate', methods=['POST'])
@csrf.exempt
@login_required
def terminate_alert(identifier):
    """End a dispatched alert (CAP Cancel) — the emergency is resolved.

    Body: {reason: str}
    """
    if session['user'].get('role') not in _LIFECYCLE_ROLES:
        return jsonify({"error": "Unauthorized"}), 403

    alert = find_alert_by_identifier(identifier)
    if not alert:
        return jsonify({"error": "Alert not found"}), 404
    if alert.get('workflow_stage') != 3:
        return jsonify({"error": "Only dispatched alerts can be terminated"}), 400
    if alert.get('lifecycle') == 'terminated':
        return jsonify({"error": "Alert already terminated"}), 409

    data = request.get_json(silent=True) or {}
    reason = (data.get('reason') or '').strip() or 'No reason provided'
    now = datetime.now(timezone.utc).isoformat()
    actor = session['user']

    history_entry = {
        "action": "terminate",
        "by": actor.get('name'),
        "by_email": actor.get('email'),
        "by_role": actor.get('role'),
        "at": now,
        "reason": reason,
    }
    history = list(alert.get('lifecycle_history') or [])
    history.append(history_entry)

    patch = {
        "lifecycle": "terminated",
        "lifecycle_history": history,
        "terminated_by": actor.get('name'),
        "terminated_at": now,
        "terminated_reason": reason,
        "msgType": "Cancel",
    }
    update_alert_workflow(identifier, 3, patch)

    # Reload the alert with the patch applied to get a consistent snapshot.
    updated = find_alert_by_identifier(identifier) or {**alert, **patch}
    _broadcast_alert_update(updated)
    logging.info("Alert %s terminated by %s. Reason: %s", identifier, actor.get('email'), reason)
    return jsonify({"status": "success", "message": "Alert terminated", "alert": updated}), 200


@app.route('/api/v1/alerts/<identifier>/extend', methods=['POST'])
@csrf.exempt
@login_required
def extend_alert(identifier):
    """Update / extend a dispatched alert (CAP Update) — the emergency has
    worsened or new information has come in.

    Body: {
        reason: str,
        severity?: 'Extreme'|'Severe'|'Moderate'|'Minor',
        appended_description?: str,
    }
    """
    if session['user'].get('role') not in _LIFECYCLE_ROLES:
        return jsonify({"error": "Unauthorized"}), 403

    alert = find_alert_by_identifier(identifier)
    if not alert:
        return jsonify({"error": "Alert not found"}), 404
    if alert.get('workflow_stage') != 3:
        return jsonify({"error": "Only dispatched alerts can be extended"}), 400
    if alert.get('lifecycle') == 'terminated':
        return jsonify({"error": "Cannot extend a terminated alert"}), 409

    data = request.get_json(silent=True) or {}
    reason = (data.get('reason') or '').strip() or 'No reason provided'
    new_severity = data.get('severity')
    appended = (data.get('appended_description') or '').strip()
    valid_sev = {'Extreme', 'Severe', 'Moderate', 'Minor'}
    if new_severity and new_severity not in valid_sev:
        return jsonify({"error": "Invalid severity"}), 400

    now = datetime.now(timezone.utc).isoformat()
    actor = session['user']
    prev_severity = alert.get('severity')

    history_entry = {
        "action": "extend",
        "by": actor.get('name'),
        "by_email": actor.get('email'),
        "by_role": actor.get('role'),
        "at": now,
        "reason": reason,
        "severity_before": prev_severity,
        "severity_after": new_severity or prev_severity,
    }
    history = list(alert.get('lifecycle_history') or [])
    history.append(history_entry)

    extension_count = (alert.get('extension_count') or 0) + 1
    patch = {
        "lifecycle": "extended",
        "lifecycle_history": history,
        "extended_by": actor.get('name'),
        "extended_at": now,
        "extension_reason": reason,
        "extension_count": extension_count,
        "msgType": "Update",
    }
    if new_severity:
        patch["severity"] = new_severity
    if appended:
        existing_desc = (alert.get('description') or '').rstrip()
        patch["description"] = f"{existing_desc}\n\n[UPDATE {now}] {appended}" if existing_desc else appended

    update_alert_workflow(identifier, 3, patch)
    updated = find_alert_by_identifier(identifier) or {**alert, **patch}
    _broadcast_alert_update(updated)
    logging.info(
        "Alert %s extended by %s (severity %s → %s). Reason: %s",
        identifier, actor.get('email'), prev_severity, patch.get('severity', prev_severity), reason,
    )
    return jsonify({"status": "success", "message": "Alert extended", "alert": updated}), 200


# Phase 8: in-memory cache of the most recent dispatched alert. Used by
# /public/feed/display to render an initial state when a new client connects
# and by the /live_feed Socket.IO namespace to bootstrap subscribers.
_latest_public_alert = None


@app.route('/public/feed/receive', methods=['POST'])
@csrf.exempt  # public endpoint, no session
@limiter.limit("60 per minute")
def public_feed_receive():
    """Phase 8: receives the dispatched MNO payload from
    `dispatch_service.dispatch_to_mno` (which defaults to this URL when
    MNO_WEBHOOK_URL isn't configured). Caches the latest alert and broadcasts
    it on the /live_feed Socket.IO namespace so connected TV displays update
    in real time."""
    global _latest_public_alert
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "JSON body required"}), 400
    _latest_public_alert = data
    socketio.emit('alert', data, namespace='/live_feed')
    logging.info("Public feed received alert %s; broadcast on /live_feed.", data.get('identifier'))
    return jsonify({"status": "received", "identifier": data.get('identifier')}), 200


@app.route('/public/feed/display')
@limiter.limit("120 per minute")
def public_feed_display():
    """Phase 8: full-screen TV-style page showing the latest dispatched alert.
    Public, no login. Subscribes to /live_feed namespace for real-time
    updates. Optional ?viewer=<token> reserved for signed-token embeds."""
    return render_template('public_feed.html', alert=_latest_public_alert)


@socketio.on('connect', namespace='/live_feed')
def _on_live_feed_connect():
    """Bootstrap newly-connected TV displays with the current latest alert."""
    if _latest_public_alert:
        emit('alert', _latest_public_alert)


@app.route('/api/v1/agents/draft', methods=['POST'])
@csrf.exempt  # JSON endpoint; Phase 4 frontend will move to token-in-header
@login_required
@limiter.limit("30 per hour")
def agents_draft():
    """Phase 6: AI advisory agent. Free-form text in → CAP-shaped JSON draft
    out for human review/edit on the Manual Entry tab."""
    data = request.get_json(silent=True) or {}
    user_text = (data.get('text') or '').strip()
    if not user_text:
        return jsonify({"error": "text field is required"}), 400
    draft = advisory_agent_service.draft_cap(user_text)
    if 'error' in draft and 'agent' not in draft:
        return jsonify(draft), 502
    return jsonify(draft), 200


# Heuristic radii by inferred place granularity. The agent reads the
# location string + the geocoder hit's place "type" and picks one bucket so
# the operator gets a sensible affected-area circle even when they don't
# specify a radius themselves.
_RADIUS_BUCKETS = {
    "spot":         2.0,    # specific landmark, intersection, beach
    "neighbourhood": 4.0,   # Osu, Dzorwulu, Adabraka
    "town":         12.0,   # Ho, Wa, Cape Coast
    "city":         28.0,   # Accra, Kumasi, Tamale
    "metropolis":   55.0,   # Greater Accra metro
    "district":     35.0,
    "region":       95.0,
    "country":      280.0,
}

_NEIGHBOURHOOD_HINTS = {
    "osu", "dzorwulu", "adabraka", "labadi", "labone", "cantonments",
    "east legon", "west legon", "airport residential", "ridge", "kaneshie",
    "tema", "spintex", "madina", "ashaiman",
}
_CITY_HINTS = {"accra", "kumasi", "tamale", "sekondi", "takoradi", "lagos", "abidjan", "lome"}
_REGION_HINTS = {"region", "metropolitan", "metro", "greater"}


def _infer_radius_km(text: str, geocoded: dict) -> tuple[float, str]:
    """Return (radius_km, granularity_label) inferred from the description +
    geocoder result. Pure-Python rule set; no LLM call needed."""
    t = (text or "").lower()
    place_type = (geocoded.get("type") or "").lower()
    name = (geocoded.get("name") or "").lower()

    if any(h in t or h in name for h in _NEIGHBOURHOOD_HINTS):
        return _RADIUS_BUCKETS["neighbourhood"], "neighbourhood"
    if any(h in t for h in _REGION_HINTS):
        return _RADIUS_BUCKETS["region"], "region"
    if place_type in {"city", "town"} or any(h in name for h in _CITY_HINTS):
        return _RADIUS_BUCKETS["city"], "city"
    if place_type in {"village", "hamlet", "suburb", "neighbourhood"}:
        return _RADIUS_BUCKETS["neighbourhood"], "neighbourhood"
    if place_type in {"administrative", "boundary"}:
        return _RADIUS_BUCKETS["region"], "region"
    if place_type in {"island", "river", "peak", "natural"}:
        return _RADIUS_BUCKETS["spot"], "landmark"
    # Static-geocoder hits with type='neighbourhood'/'town'/'capital'
    if "neighbourhood" in (geocoded.get("type") or ""):
        return _RADIUS_BUCKETS["neighbourhood"], "neighbourhood"
    if "capital" in (geocoded.get("type") or ""):
        return _RADIUS_BUCKETS["city"], "city"
    return _RADIUS_BUCKETS["town"], "town"


@app.route('/api/v1/agents/area', methods=['POST'])
@csrf.exempt
@login_required
@limiter.limit("60 per hour")
def agents_area():
    """Resolve {location, description, radius_km?} → bounded area for the
    map. The agent geocodes the location (static table → Nominatim fallback),
    picks a sensible radius from the place granularity if the operator
    didn't supply one, and returns the data the Confirmation modal needs to
    render the zoomed map + alert-type animation."""
    from services.advisory_agent_service import _tool_geocode_ghana_location

    data = request.get_json(silent=True) or {}
    location = (data.get('location') or '').strip()
    description = (data.get('description') or '').strip()
    radius_km_raw = data.get('radius_km')

    # Caller can pass either field; fall back to the description if no
    # discrete location was given.
    geocode_input = location or description
    if not geocode_input:
        return jsonify({"error": "location or description required"}), 400

    geocoded = _tool_geocode_ghana_location(geocode_input)
    if geocoded.get('error'):
        return jsonify({
            "error": "could_not_resolve",
            "input": geocode_input,
            "detail": geocoded,
        }), 404

    # Honour an explicit non-zero radius from the operator; otherwise infer.
    radius_source = "user"
    try:
        radius_km = float(radius_km_raw) if radius_km_raw not in (None, '', 0, '0') else 0.0
    except (TypeError, ValueError):
        radius_km = 0.0
    if radius_km <= 0:
        radius_km, granularity = _infer_radius_km(geocode_input, geocoded)
        radius_source = f"agent ({granularity})"

    # Light event-type sniff so the map can pick the correct animation overlay
    # without a second round-trip.
    text = f"{description} {location}".lower()
    event_type = "alert"
    for kw in ("flood", "rain", "storm", "fire", "earthquake", "drought", "heat", "cholera"):
        if kw in text:
            event_type = kw
            break

    return jsonify({
        "lat": geocoded.get("lat"),
        "lon": geocoded.get("lng"),
        "radius_km": round(radius_km, 2),
        "radius_source": radius_source,
        "region": geocoded.get("region"),
        "district": geocoded.get("district"),
        "label": geocoded.get("name") or geocode_input,
        "event_type": event_type,
        "geocoder": geocoded.get("source"),
    }), 200


@app.route('/api/v1/admin/stakeholders', methods=['GET'])
@csrf.exempt
@login_required
def admin_stakeholders():
    """Catalog of emergency-services stakeholders. Available to any
    authenticated user so non-superuser screens can render an agency badge,
    but write operations (creating users) are still gated to Super Admin."""
    return jsonify({"stakeholders": EMERGENCY_STAKEHOLDERS}), 200


@app.route('/api/v1/admin/users', methods=['GET'])
@csrf.exempt
@login_required
@super_admin_required
def admin_list_users():
    """Super Admin: list all operator records (passwords stripped)."""
    users = list_users()
    return jsonify({"users": users}), 200


@app.route('/api/v1/admin/users', methods=['POST'])
@csrf.exempt
@login_required
@super_admin_required
@limiter.limit("60 per hour")
def admin_create_user():
    """Super Admin: onboard a new operator. Body:
        {email, name, agency, role, phone_number?, staff_id?, password?}
    `role` must be one of: cap generator, cap validator, Admin.
    `agency` should be a stakeholder id from EMERGENCY_STAKEHOLDERS, but free
    text is tolerated so the catalog can grow without a redeploy.
    """
    data = request.get_json(silent=True) or {}
    role = (data.get('role') or '').strip()
    agency = (data.get('agency') or '').strip()
    if agency and agency not in _STAKEHOLDER_IDS:
        # Allow free text but flag it in the response so the UI can warn.
        unknown_agency = True
    else:
        unknown_agency = False

    user, err = create_user(
        email=data.get('email'),
        name=data.get('name'),
        agency=agency,
        role=role,
        phone_number=(data.get('phone_number') or None),
        staff_id=data.get('staff_id'),
        password=data.get('password'),
        created_by=session['user'].get('email'),
    )
    if err:
        status = 409 if err == "email_exists" else 400 if err.endswith('_required') or err == 'invalid_role' else 500
        return jsonify({"error": err}), status
    response = {"status": "created", "user": user}
    if unknown_agency:
        response["warning"] = "Agency not in stakeholder catalog; stored verbatim."
    return jsonify(response), 201


def _coord_or_default(value, default):
    """Tolerate empty strings, None, or non-numeric values by falling back to default.
    The manual form ships empty hidden inputs for lat/lon until the user clicks the
    map; passing those directly to float() raises ValueError."""
    if value is None or value == '':
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def process_alert_logic(data, sender_info=None, client_ip="Unknown", workflow_stage=1):
    """Core logic to process, enrich, and (conditionally) dispatch alerts"""
    try:
        alert_id = data.get('identifier', f"GH-CAP-{uuid.uuid4().hex[:8].upper()}")
        lat = _coord_or_default(data.get('latitude'), 5.6037)
        lon = _coord_or_default(data.get('longitude'), -0.1870)
        
        # Geo-Resolution
        affected_regions = geo_service.resolve_location(lat, lon)
        
        # Enrichment
        english_text = data.get('description', '')
        translations = enrichment_service.translate_text(english_text, ["Twi", "Hausa"])
        
        audio_links = {}
        for lang, text in translations.items():
            audio_links[lang] = enrichment_service.text_to_speech(text, lang)
            
        enriched_alert = {
            "identifier": alert_id,
            "sender_name": sender_info.get('name') if sender_info else "System",
            "sender_agency": sender_info.get('agency') if sender_info else "System",
            "sender_id": sender_info.get('staff_id') if sender_info else "Unknown",
            "sender_ip": client_ip,
            "sent": datetime.now(timezone.utc).isoformat(),
            "status": data.get('status', 'Actual'),
            "msgType": data.get('msgType', 'Alert'),
            "scope": data.get('scope', 'Public'),
            "category": data.get('category', 'Met'),
            "event": data.get('event', 'Weather Alert'),
            "urgency": data.get('urgency', 'Immediate'),
            "severity": data.get('severity', 'Severe'),
            "certainty": data.get('certainty', 'Observed'),
            "headline": data.get('headline', 'Emergency Alert'),
            "description": english_text,
            "instruction": data.get('instruction', ''),
            "affected_regions": affected_regions,
            "translations": translations,
            "audio_links": audio_links,
            "geo": {"lat": lat, "lon": lon},
            "mno_dispatched": False,
            "sms_sent": False,
            "workflow_stage": workflow_stage
        }
        
        # ONLY Dispatch if workflow_stage is 3 (Immediate Dispatch for Admins/Auto)
        if workflow_stage == 3:
            enriched_alert['mno_dispatched'] = dispatch_service.dispatch_to_mno(enriched_alert)
            sms_text = f"ALERT: {enriched_alert['headline']}\n{translations.get('English', english_text)}"
            recipients = data.get('recipients', ["+233540000000"]) 
            enriched_alert['sms_sent'] = dispatch_service.send_sms(sms_text, recipients)
        
        save_alert(enriched_alert)
        socketio.emit('new_alert', enriched_alert)
        
        # Sync to external analytics
        external_analytics_service.sync_alert(enriched_alert)
        
        msg = "Alert submitted for validation" if workflow_stage == 1 else "Alert dispatched"
        return jsonify({"status": "success", "identifier": alert_id, "message": msg}), 201
    except Exception as e:
        logging.error(f"Alert processing failed: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    os.makedirs(os.path.join("static", "audio"), exist_ok=True)
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', '1') != '0'
    use_reloader = os.environ.get('FLASK_USE_RELOADER', '1') != '0' and debug
    print(f"\n * Dashboard: http://localhost:{port}")
    print(f" * Login: http://localhost:{port}/login\n")
    socketio.run(app, host='0.0.0.0', port=port, debug=debug, use_reloader=use_reloader)
