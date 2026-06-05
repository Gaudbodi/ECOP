"""Shared pytest fixtures for the Ghana CAP Platform test suite (Phase 9).

Strategy:
- Tests run against the Flask test client; no real server.
- External integrations are exercised in graceful-degradation mode (no creds
  set), which is the documented invariant — the suite must boot and pass
  without OPENAI_API_KEY / ANTHROPIC_API_KEY / AT credentials.
- The MongoDB connection succeeds (the live URI is in db.py as a fallback);
  tests touching alerts use unique identifiers to avoid collision and clean
  up where appropriate.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure the project root is importable as a package root.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="session")
def app():
    """Boot the Flask app once per session. Disable CSRF for the test client
    so JSON tests don't need to thread tokens (the production app keeps CSRF
    on form routes; this fixture only exempts during tests)."""
    import ghana_cap_app
    ghana_cap_app.app.config["TESTING"] = True
    ghana_cap_app.app.config["WTF_CSRF_ENABLED"] = False
    # Disable per-route Limiter checks during tests so brute-force tests
    # don't trip the global decorators set in ghana_cap_app.py.
    ghana_cap_app.limiter.enabled = False
    return ghana_cap_app.app


@pytest.fixture
def client(app):
    """Plain anonymous test client."""
    with app.test_client() as c:
        yield c


@pytest.fixture
def auth_client(app):
    """Test client with a logged-in admin session (bypasses email/SMS 2FA)."""
    with app.test_client() as c:
        with c.session_transaction() as s:
            s["user"] = {
                "staff_id": "E004",
                "name": "Francis Yiryel",
                "agency": "NCA",
                "role": "Admin",
                "email": "francis@example.com",
            }
        yield c


@pytest.fixture
def sample_dispatch_payload():
    """Representative MNO-dispatched alert payload."""
    return {
        "identifier": "TEST-PHASE9-001",
        "headline": "Heavy Rain Expected at Osu",
        "description": "Heavy rainfall over Greater Accra in the next 6 hours.",
        "event": "Rain",
        "category": "Met",
        "severity": "Severe",
        "urgency": "Immediate",
        "certainty": "Likely",
        "sender_agency": "GMeT",
        "sent": "2026-05-09T15:00:00Z",
        "affected_regions": ["Greater Accra Region"],
        "audio_links": {
            "English": "/static/audio/mock_english.mp3",
            "Twi": "/static/audio/mock_twi.mp3",
            "Hausa": "/static/audio/mock_hausa.mp3",
        },
        "geo": {"lat": 5.5567, "lon": -0.182},
    }
