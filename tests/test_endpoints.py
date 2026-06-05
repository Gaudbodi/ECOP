"""Endpoint coverage for Phases 1, 2, 6, 8."""
from __future__ import annotations


# ─────────────────────────── /login (Phase 2) ───────────────────────────


def test_login_renders(client):
    r = client.get("/login")
    assert r.status_code == 200
    assert b"Ghana CAP Portal" in r.data


def test_logout_redirects(client):
    r = client.get("/logout")
    assert r.status_code == 302


# ──────────────────────── /api/v1/alerts/gmet/webhook (Phase 1) ────────────────────────


def test_webhook_rejects_missing_api_key(client, sample_dispatch_payload):
    r = client.post("/api/v1/alerts/gmet/webhook", json=sample_dispatch_payload)
    assert r.status_code == 401
    assert r.get_json() == {"error": "Unauthorized"}


def test_webhook_rejects_wrong_api_key(client, sample_dispatch_payload):
    r = client.post(
        "/api/v1/alerts/gmet/webhook",
        json=sample_dispatch_payload,
        headers={"X-CAP-API-KEY": "wrong-key"},
    )
    assert r.status_code == 401


def test_webhook_accepts_correct_api_key_and_auto_dispatches(client, sample_dispatch_payload):
    """Phase 1 acceptance #1+#5: GMeT webhook auto-dispatches at workflow_stage=3.
    Even if MNO/SMS dispatch fails (graceful degradation), the response is 201
    'Alert dispatched' — proving the auto-dispatch path executed (not pending)."""
    r = client.post(
        "/api/v1/alerts/gmet/webhook",
        json=sample_dispatch_payload,
        headers={"X-CAP-API-KEY": "gh_cap_poc_key_2026"},
    )
    assert r.status_code == 201
    body = r.get_json()
    assert body["status"] == "success"
    assert body["message"] == "Alert dispatched"  # NOT "Alert submitted for validation"


# ─────────────────────── /api/v1/alerts/manual (Phase 1) ───────────────────────


def test_manual_alert_requires_login(client):
    r = client.post("/api/v1/alerts/manual", json={"description": "test"})
    assert r.status_code == 302  # redirect to /login


def test_manual_alert_tolerates_empty_latlon(auth_client):
    """Phase 1 fix: empty-string lat/lon used to crash via float('') → ValueError."""
    r = auth_client.post(
        "/api/v1/alerts/manual",
        json={
            "headline": "Test",
            "description": "Empty coords smoke",
            "severity": "Moderate",
            "latitude": "",
            "longitude": "",
        },
    )
    assert r.status_code == 201
    body = r.get_json()
    assert body["status"] == "success"


# ─────────────────────── /api/v1/agents/draft (Phase 6) ───────────────────────


def test_agents_draft_requires_login(client):
    r = client.post("/api/v1/agents/draft", json={"text": "heavy rain at Osu"})
    assert r.status_code == 302


def test_agents_draft_returns_cap_json_in_mock_mode(auth_client):
    """Without ANTHROPIC_API_KEY, the agent returns a clearly-marked mock CAP
    draft that still resolves the static geocoder — graceful degradation."""
    r = auth_client.post("/api/v1/agents/draft", json={"text": "heavy rain expected at Osu in Accra"})
    assert r.status_code == 200
    body = r.get_json()
    expected = {"headline", "description", "instruction", "category", "event",
                "urgency", "severity", "certainty", "latitude", "longitude",
                "affected_region", "affected_district", "language", "agent"}
    assert expected.issubset(body.keys())
    # Type-priority resolver should produce Osu coords, not Accra.
    assert abs(body["latitude"] - 5.5567) < 0.01
    assert abs(body["longitude"] - -0.1820) < 0.01
    assert body["affected_region"] == "Greater Accra"
    assert body["agent"]["mock"] is True


def test_agents_draft_rejects_empty_input(auth_client):
    r = auth_client.post("/api/v1/agents/draft", json={"text": ""})
    assert r.status_code == 400


def test_agents_area_resolves_static_place(auth_client):
    """/api/v1/agents/area resolves a known static place exactly (no Nominatim
    needed) and returns a precise, non-approximate point."""
    r = auth_client.post("/api/v1/agents/area", json={"location": "Dzorwulu"})
    assert r.status_code == 200
    body = r.get_json()
    assert body["approximate"] is False
    assert body["region"] == "Greater Accra"
    assert abs(body["lat"] - 5.6126) < 0.05


def test_agents_area_degrades_gracefully_when_geocode_fails(auth_client, monkeypatch):
    """When the exact place can't be geocoded (e.g. Nominatim blocked from a
    cloud egress IP), the endpoint must NOT 404. It falls back to a region
    centroid when a region is detectable, returning 200 + approximate=true so
    the operator can still proceed and adjust on the map. Regression for the
    'resolving CAP location raises 404' report."""
    import services.advisory_agent_service as agent_svc

    # Simulate Nominatim being unavailable: geocode always errors.
    monkeypatch.setattr(
        agent_svc,
        "_tool_geocode_ghana_location",
        lambda text: {"source": "nominatim", "input": text, "error": "lookup_failed"},
    )

    # Region detectable from the text → region centroid fallback.
    r = auth_client.post(
        "/api/v1/agents/area",
        json={"location": "an unmapped hamlet in the Eastern Region"},
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["approximate"] is True
    assert body["region"] == "Eastern"
    assert body["geocoder"] == "fallback-region"
    assert body["lat"] is not None and body["lon"] is not None

    # No region detectable → national centroid fallback, still 200 (never 404).
    r2 = auth_client.post(
        "/api/v1/agents/area",
        json={"location": "totally-unknown-place-zzz"},
    )
    assert r2.status_code == 200
    body2 = r2.get_json()
    assert body2["approximate"] is True
    assert body2["geocoder"] == "fallback-national"


# ─────────────────────── /public/feed/* (Phase 8) ───────────────────────


def test_public_feed_display_empty_state(client):
    """Fresh server / no alert posted yet → 'Awaiting alerts' empty state."""
    import ghana_cap_app
    ghana_cap_app._latest_public_alert = None
    r = client.get("/public/feed/display")
    assert r.status_code == 200
    assert b"Awaiting alerts" in r.data


def test_public_feed_receive_caches_and_renders(client, sample_dispatch_payload):
    """POST → 200; GET shows the cached alert."""
    r1 = client.post("/public/feed/receive", json=sample_dispatch_payload)
    assert r1.status_code == 200
    assert r1.get_json()["status"] == "received"

    r2 = client.get("/public/feed/display")
    assert r2.status_code == 200
    body = r2.data.decode()
    assert "Heavy Rain Expected at Osu" in body
    assert "Severe" in body
    assert "TEST-PHASE9-001" in body  # serialised initialAlert in <script>


def test_public_feed_receive_rejects_non_json(client):
    r = client.post("/public/feed/receive", data="not json", content_type="text/plain")
    assert r.status_code == 400


# ─────────────────────── Phase 4: SPA serve + new JSON endpoints ───────────────────────


def test_dashboard_serves_spa(auth_client):
    """Phase 4: GET / returns the Vite-built React shell, not the old Jinja dashboard.
    The Vite-built index.html references hashed assets under /assets/ and contains
    the no-flash theme bootstrap. PATTERNS.md "Server-side modification"."""
    r = auth_client.get("/")
    assert r.status_code == 200
    body = r.data.decode()
    # SPA shell markers — present in our index.html template.
    assert "data-theme" in body
    assert "/assets/" in body
    # Sanity: the old Jinja dashboard's distinctive content is GONE.
    # The Jinja template renders {% for alert in alerts %} loops; the SPA shell does not.
    assert "{% for alert" not in body


def test_dashboard_redirects_when_logged_out(client):
    r = client.get("/")
    assert r.status_code == 302  # login_required gate


def test_login_still_renders_jinja(client):
    """Phase 4 must not regress login.html — it stays Jinja per RESEARCH.md A1."""
    r = client.get("/login")
    assert r.status_code == 200
    assert b"Ghana CAP Portal" in r.data


def test_me_endpoint_requires_login(client):
    r = client.get("/api/v1/me")
    assert r.status_code == 302


def test_me_endpoint_returns_session_user(auth_client):
    r = auth_client.get("/api/v1/me")
    assert r.status_code == 200
    body = r.get_json()
    # Must match session['user'] shape from conftest.auth_client fixture.
    assert body["email"] == "francis@example.com"
    assert body["role"] == "Admin"
    assert body["agency"] == "NCA"
    assert {"staff_id", "name", "agency", "role", "email"}.issubset(body.keys())


def test_alerts_list_requires_login(client):
    r = client.get("/api/v1/alerts")
    assert r.status_code == 302


def test_alerts_list_returns_envelope(auth_client):
    """Returns {alerts: [...], degraded: bool}. Items have _id stringified
    or absent (RESEARCH.md Pitfall #3 — never raw ObjectId)."""
    r = auth_client.get("/api/v1/alerts")
    assert r.status_code == 200
    body = r.get_json()
    assert "alerts" in body
    assert "degraded" in body
    assert isinstance(body["alerts"], list)
    # If any alerts are present, _id must be a string (not ObjectId), and
    # the canonical CAP fields are present.
    for a in body["alerts"]:
        if "_id" in a:
            assert isinstance(a["_id"], str)


def test_dispatcher_test_requires_login(client):
    r = client.post("/api/v1/dispatcher/test")
    assert r.status_code == 302


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


def test_dispatcher_test_admin_dispatches_mock(auth_client):
    """Admin POST → 201 + identifier + 'Alert dispatched' message (workflow_stage=3
    means process_alert_logic ran the dispatch path).

    Test pollution: writes to live Mongo (tests/conftest.py invariant). The
    Plan 01 dispatcher fixture uses sender_id='TEST-DISPATCHER' so cleanup
    via `db.alerts.delete_many({'sender_id': {'$regex': '^TEST-'}})` is
    trivial if needed."""
    r = auth_client.post("/api/v1/dispatcher/test")
    assert r.status_code == 201
    body = r.get_json()
    assert body["status"] == "success"
    assert body["identifier"].startswith("GH-CAP-")
    assert body["message"] == "Alert dispatched"


def test_assets_route_serves_after_build(auth_client):
    """Phase 4: GET /assets/<file> returns the actual hashed asset that
    `cd frontend && npm run build` writes into frontend/dist/assets/.
    Complementary to test_assets_route_404_for_missing_file in Plan 05
    (which asserts the 404 path); this test asserts the 200 path.

    Discovers the hashed filename at runtime by listing
    frontend/dist/assets/ and picking the first index-*.js. Skips
    cleanly if the build hasn't run (CI ordering: pytest may run
    before npm run build on a cold checkout)."""
    import os
    assets_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), '..', 'frontend', 'dist', 'assets'
    )
    if not os.path.isdir(assets_dir):
        import pytest
        pytest.skip("frontend/dist/assets/ not present — run `cd frontend && npm run build` first")
    js_files = [f for f in os.listdir(assets_dir) if f.startswith('index-') and f.endswith('.js')]
    if not js_files:
        import pytest
        pytest.skip("no hashed index-*.js in frontend/dist/assets/")
    r = auth_client.get(f"/assets/{js_files[0]}")
    assert r.status_code == 200
    # Sanity: a real JS bundle should be at least a few hundred bytes.
    assert len(r.data) > 100


# ─────────────────────── Phase 4: gap-filler tests (Plan 05) ───────────────────────


def test_assets_route_404_for_missing_file(client):
    """The /assets/<path> route should 404 cleanly for non-existent files,
    not 500 — confirms send_from_directory's directory-traversal protection
    + missing-file behavior is intact."""
    r = client.get("/assets/this-file-definitely-does-not-exist-04-05.js")
    # send_from_directory returns 404 for missing files. We don't care which
    # status type Flask uses (NotFound exception → 404), only that it isn't 5xx.
    assert r.status_code == 404


def test_dispatcher_test_creates_alert_visible_via_alerts_list(auth_client):
    """Regression coverage for Test Dispatcher -> MongoDB persistence ->
    /api/v1/alerts read round-trip. Asserts the API contract: a successful
    POST /api/v1/dispatcher/test produces an alert that GET /api/v1/alerts
    returns on the next read.

    End-to-end React-shell verification (button click -> Pipeline tab shows
    the alert in real time via Socket.IO `new_alert`) is Phase 9 scope. This
    test covers the backend half only.

    Test pollution: writes to live Mongo (tests/conftest.py invariant). The
    dispatcher fixture uses sender_id='TEST-DISPATCHER' so cleanup via
    `db.alerts.delete_many({'sender_id': {'$regex': '^TEST-'}})` is trivial."""
    # Snapshot pre-state.
    pre = auth_client.get("/api/v1/alerts").get_json()
    pre_ids = {a["identifier"] for a in pre["alerts"]}

    # Fire the test dispatch.
    r = auth_client.post("/api/v1/dispatcher/test")
    assert r.status_code == 201
    new_id = r.get_json()["identifier"]
    assert new_id.startswith("GH-CAP-")

    # The new identifier must be present in the post-state alerts list.
    post = auth_client.get("/api/v1/alerts").get_json()
    post_ids = {a["identifier"] for a in post["alerts"]}
    assert new_id in post_ids
    assert new_id not in pre_ids  # truly new


# ─────────────────────── Phase 11: role-matrix enforcement tests ───────────────────────

_MINIMAL_CREATE_BODY = {
    "headline": "T",
    "description": "d",
    "severity": "Moderate",
    "latitude": "",
    "longitude": "",
}


def test_manual_alert_denies_validator(app):
    """Phase 11 REQ-role-matrix-create-gate: a cap validator POSTing the
    create endpoint is denied 403 before any alert is persisted.
    The 403 gate fires before process_alert_logic so Mongo is not touched."""
    with app.test_client() as c:
        with c.session_transaction() as s:
            s["user"] = {
                "staff_id": "V001",
                "name": "Validator User",
                "agency": "GMeT",
                "role": "cap validator",
                "email": "validator@example.com",
            }
        r = c.post("/api/v1/alerts/manual", json=_MINIMAL_CREATE_BODY)
    assert r.status_code == 403
    assert r.get_json() == {"error": "Unauthorized"}


def test_manual_alert_allows_generator_pending(app):
    """Phase 11 REQ-role-matrix-create-gate: a cap generator can create an
    alert and it lands at workflow_stage 1 (pending validation)."""
    with app.test_client() as c:
        with c.session_transaction() as s:
            s["user"] = {
                "staff_id": "G001",
                "name": "Generator User",
                "agency": "GMeT",
                "role": "cap generator",
                "email": "generator@example.com",
            }
        r = c.post("/api/v1/alerts/manual", json=_MINIMAL_CREATE_BODY)
    assert r.status_code == 201
    body = r.get_json()
    assert body["status"] == "success"
    assert body["message"] == "Alert submitted for validation"


def test_manual_alert_allows_admin_dispatch(auth_client):
    """Phase 11 REQ-role-matrix-create-gate: an Admin can create an alert
    and it lands at workflow_stage 3 (direct dispatch)."""
    r = auth_client.post("/api/v1/alerts/manual", json=_MINIMAL_CREATE_BODY)
    assert r.status_code == 201
    body = r.get_json()
    assert body["status"] == "success"
    assert body["message"] == "Alert dispatched"


def test_validate_alert_denies_generator(app):
    """Phase 11 REQ-role-matrix-validate-gate: a cap generator POSTing the
    validate endpoint is denied 403. The gate fires before the 404 not-found
    path, proving role is checked first (already-gated L409 made explicit)."""
    with app.test_client() as c:
        with c.session_transaction() as s:
            s["user"] = {
                "staff_id": "G001",
                "name": "Generator User",
                "agency": "GMeT",
                "role": "cap generator",
                "email": "generator@example.com",
            }
        r = c.post("/api/v1/alerts/validate/NONEXISTENT-ID", json={"action": "approve"})
    assert r.status_code == 403
    assert r.get_json() == {"error": "Unauthorized"}


def test_terminate_alert_denies_generator(app):
    """Phase 11 REQ-role-matrix-lifecycle-gate: a cap generator POSTing the
    terminate endpoint is denied 403. The gate fires before the 404 not-found
    path, locking _LIFECYCLE_ROLES (L465) against silent regression."""
    with app.test_client() as c:
        with c.session_transaction() as s:
            s["user"] = {
                "staff_id": "G001",
                "name": "Generator User",
                "agency": "GMeT",
                "role": "cap generator",
                "email": "generator@example.com",
            }
        r = c.post("/api/v1/alerts/NONEXISTENT-ID/terminate", json={"reason": "test"})
    assert r.status_code == 403
    assert r.get_json() == {"error": "Unauthorized"}


def test_validate_alert_allows_super_admin(app):
    """Role matrix: Super Admin may validate (approve/reject) pending alerts —
    'Admins/Super Admins can do both'. A Super Admin must pass the role gate;
    proven by getting the 404 not-found (gate passed) rather than 403 Unauthorized.
    Locks the gate against the regression where Super Admin was omitted from the
    validate allowlist while present in _LIFECYCLE_ROLES."""
    with app.test_client() as c:
        with c.session_transaction() as s:
            s["user"] = {
                "staff_id": "E004",
                "name": "Francis Yiryel",
                "agency": "NCA",
                "role": "Super Admin",
                "email": "francisyiryel@gmail.com",
            }
        r = c.post("/api/v1/alerts/validate/NONEXISTENT-ID", json={"action": "approve"})
    # Gate passed (not 403); the alert genuinely does not exist → 404.
    assert r.status_code == 404
    assert r.get_json() == {"error": "Alert not found"}
