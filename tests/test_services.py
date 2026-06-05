"""Service-level coverage for Phases 1, 3, 6 (graceful-degradation paths)."""
from __future__ import annotations


# ──────────────────────────── geo_service ────────────────────────────


def test_geo_service_resolves_accra_to_greater_accra():
    from services.geo_service import geo_service

    affected = geo_service.resolve_location(5.6037, -0.1870)
    assert isinstance(affected, list)
    assert any("Accra" in r for r in affected)


def test_geo_service_outside_ghana_falls_back():
    from services.geo_service import geo_service

    affected = geo_service.resolve_location(0, 0)
    assert affected == ["Ghana (General)"]


# ─────────────────────── _ghana_reference.lookup_place ───────────────────────


def test_lookup_place_type_priority_picks_neighborhood_over_city():
    from services._ghana_reference import lookup_place

    result = lookup_place("heavy rain expected at Osu in Accra")
    assert result is not None
    assert result["name"] == "osu"
    assert result["type"] == "neighborhood"


def test_lookup_place_returns_city_when_only_city_matches():
    from services._ghana_reference import lookup_place

    result = lookup_place("flood in Tamale")
    assert result is not None
    assert result["name"] == "tamale"
    assert result["type"] == "city"


def test_lookup_place_returns_none_for_unknown():
    from services._ghana_reference import lookup_place

    assert lookup_place("Lagos Nigeria") is None


# ──────────────────────── enrichment_service ────────────────────────


def test_enrichment_translation_mock_when_no_key(monkeypatch):
    """OPENAI_API_KEY missing → mock translations preserve graceful degradation."""
    monkeypatch.setenv("OPENAI_API_KEY", "")
    from services.enrichment_service import EnrichmentService

    es = EnrichmentService()
    es.openai_client = None  # force mock path regardless of singleton state
    out = es.translate_text("heavy rain", languages=["Twi", "Hausa"])
    assert out["English"] == "heavy rain"
    assert "Twi Translation Mock" in out["Twi"]
    assert "Hausa Translation Mock" in out["Hausa"]


def test_enrichment_tts_mock_when_no_provider(monkeypatch):
    """No OpenAI → mock URL, no exception. Khaya was removed in May 2026
    (ghananlp.org public API was withdrawn); OpenAI is the sole provider."""
    monkeypatch.setenv("OPENAI_API_KEY", "")
    from services.enrichment_service import EnrichmentService

    es = EnrichmentService()
    es.openai_client = None
    url = es.text_to_speech("test", "Twi")
    assert url == "/static/audio/mock_twi.mp3"


# ──────────────────────── advisory_agent_service ────────────────────────


def test_advisory_agent_geocode_tool_resolves_osu():
    from services.advisory_agent_service import _tool_geocode_ghana_location

    out = _tool_geocode_ghana_location("Osu in Accra")
    assert out["source"] == "static"
    assert out["name"] == "osu"
    assert abs(out["lat"] - 5.5567) < 0.01
    assert out["region"] == "Greater Accra"


def test_advisory_agent_population_tool_returns_density():
    from services.advisory_agent_service import _tool_lookup_population_density

    out = _tool_lookup_population_density("Greater Accra")
    assert out["region"] == "Greater Accra"
    assert out["region_population"] > 5_000_000
    assert out["region_density_per_km2"] is not None


def test_advisory_agent_severity_tool_bumps_for_rainy_season_pop_dense():
    """Rule: rain + dense population + rainy season → severity bumped from
    Moderate to Severe."""
    from services.advisory_agent_service import _tool_assess_emergency_severity

    out = _tool_assess_emergency_severity("rain", area_population=5_500_000, time_of_year="rainy-major")
    assert out["matched_keyword"] == "rain"
    assert out["severity"] in {"Severe", "Extreme"}
    assert out["bumped_for_context"] is True


def test_advisory_agent_draft_advisory_tool_uses_event_template():
    from services.advisory_agent_service import _tool_draft_cap_advisory

    out = _tool_draft_cap_advisory("flood", "Severe", "Tamale, Northern", description="River overflow")
    assert "flood" in out["headline"].lower()
    assert "higher ground" in out["instruction"].lower()


def test_advisory_agent_mock_response_uses_static_geocoder():
    """Without GEMINI_API_KEY the agent returns a mock — but the mock still
    consults the static geocoder so it's at least useful for smoke tests."""
    from services.advisory_agent_service import AdvisoryAgentService

    agent = AdvisoryAgentService()
    agent.client = None  # force mock path
    out = agent.draft_cap("heavy rain expected at Osu in Accra")
    assert out["agent"]["mock"] is True
    assert abs(out["latitude"] - 5.5567) < 0.01
    assert out["affected_region"] == "Greater Accra"
    assert "MOCK" in out["headline"]


# ──────────────────────── sms_2fa_service ────────────────────────


def test_sms_2fa_log_only_fallback(monkeypatch):
    """Without AT or Twilio creds, send_code logs and returns True (the
    same convention as email_service so the login flow proceeds in dev)."""
    monkeypatch.setenv("AFRICASTALKING_USERNAME", "")
    monkeypatch.setenv("AFRICASTALKING_API_KEY", "")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "")
    from services.sms_2fa_service import SMS2FAService

    svc = SMS2FAService()
    svc.at_client = None
    svc.twilio_client = None
    assert svc.send_code("+233000000001", "123456") is True
