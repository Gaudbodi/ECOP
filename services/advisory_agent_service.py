"""AI advisory agent — Google Gemma 4 via the Gemini API with native function calling.

Phase 6 contract:
    POST /api/v1/agents/draft  body: {"text": "<free-form alert input>"}
    →  CAP-shaped JSON populating the Manual Entry form for human review/edit.

Tools the agent has access to:
    1. geocode_ghana_location(text)         → coords + region + district
    2. lookup_population_density(region, district?) → population stats
    3. query_historical_alerts(region, event_type?) → past alerts (Mongo)
    4. assess_emergency_severity(event_type, area_population?, time_of_year?)
                                            → CAP severity / urgency / certainty
    5. draft_cap_advisory(event_type, severity, area, language="en")
                                            → headline + description + instruction

Graceful degradation: without GEMINI_API_KEY, the agent returns a clearly-marked
mock CAP draft so the endpoint and downstream UI still work.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any

import requests

from db import get_all_alerts
from services._ghana_reference import (
    PLACES,
    REGIONS,
    current_season,
    lookup_place,
    region_density,
)

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemma-4-26b-a4b-it")
NOMINATIM_USER_AGENT = "GhanaCAPPlatform/1.0 (advisory-agent)"

MAX_AGENT_TURNS = 8


def _tool_geocode_ghana_location(text: str) -> dict:
    hit = lookup_place(text)
    if hit:
        return {
            "source": "static",
            "input": text,
            "name": hit["name"],
            "lat": hit["lat"],
            "lng": hit["lng"],
            "region": hit["region"],
            "district": hit["district"],
            "type": hit["type"],
        }
    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": f"{text}, Ghana", "format": "json", "limit": 1, "countrycodes": "gh"},
            headers={"User-Agent": NOMINATIM_USER_AGENT},
            timeout=10,
        )
        resp.raise_for_status()
        rows = resp.json()
    except Exception as e:
        logger.warning("Nominatim geocode failed for %r: %s", text, e)
        return {"source": "nominatim", "input": text, "error": "lookup_failed"}
    if not rows:
        return {"source": "nominatim", "input": text, "error": "not_found"}
    row = rows[0]
    return {
        "source": "nominatim",
        "input": text,
        "name": row.get("display_name", text),
        "lat": float(row["lat"]),
        "lng": float(row["lon"]),
        "region": None,
        "district": None,
        "type": row.get("type"),
    }


def _tool_lookup_population_density(region: str, district: str | None = None) -> dict:
    region_data = REGIONS.get(region)
    if not region_data:
        return {"region": region, "error": "unknown_region", "known_regions": list(REGIONS.keys())}
    return {
        "region": region,
        "district": district,
        "region_population": region_data["population"],
        "region_area_km2": region_data["area_km2"],
        "region_density_per_km2": region_density(region),
        "district_data_available": False,
        "note": "District-level breakdown not in static table; region figure returned. Refine with district-level GeoJSON in a follow-up phase.",
    }


def _tool_query_historical_alerts(region: str, event_type: str | None = None, limit: int = 5) -> dict:
    try:
        all_alerts = get_all_alerts()
    except Exception as e:
        return {"region": region, "event_type": event_type, "error": f"db_error: {e}", "matches": []}

    matches = []
    region_l = (region or "").lower()
    et_l = (event_type or "").lower()
    for alert in all_alerts:
        affected = " ".join((alert.get("affected_regions") or [])).lower()
        if region_l and region_l not in affected:
            continue
        if et_l and et_l not in (alert.get("event") or "").lower():
            continue
        matches.append({
            "identifier": alert.get("identifier"),
            "headline": alert.get("headline"),
            "event": alert.get("event"),
            "severity": alert.get("severity"),
            "sent": alert.get("sent"),
            "affected_regions": alert.get("affected_regions"),
        })
        if len(matches) >= limit:
            break
    return {"region": region, "event_type": event_type, "match_count": len(matches), "matches": matches}


_SEVERITY_RULES = {
    "flood":            ("Extreme", "Immediate", "Likely"),
    "storm":            ("Severe", "Immediate", "Likely"),
    "rain":             ("Moderate", "Expected", "Likely"),
    "fire":             ("Extreme", "Immediate", "Observed"),
    "earthquake":       ("Extreme", "Immediate", "Observed"),
    "cholera":          ("Severe", "Expected", "Observed"),
    "drought":          ("Severe", "Future", "Likely"),
    "heat":             ("Severe", "Expected", "Likely"),
    "harmattan":        ("Moderate", "Expected", "Likely"),
}


def _tool_assess_emergency_severity(event_type: str, area_population: int | None = None, time_of_year: str | None = None) -> dict:
    et_l = (event_type or "").lower()
    severity, urgency, certainty = "Moderate", "Expected", "Likely"
    matched = None
    for keyword, baseline in _SEVERITY_RULES.items():
        if keyword in et_l:
            severity, urgency, certainty = baseline
            matched = keyword
            break

    bumped = False
    season = (time_of_year or current_season()).lower()
    if matched in {"rain", "flood"} and "rainy" in season and (area_population or 0) >= 1_000_000:
        severity = {"Moderate": "Severe", "Severe": "Extreme"}.get(severity, severity)
        bumped = True
    if matched == "fire" and "harmattan" in season:
        urgency = "Immediate"
        bumped = True

    return {
        "event_type": event_type,
        "matched_keyword": matched,
        "season": season,
        "area_population": area_population,
        "severity": severity,
        "urgency": urgency,
        "certainty": certainty,
        "bumped_for_context": bumped,
    }


_ADVISORY_TEMPLATES = {
    "flood": (
        "{severity} flood {urgency_phrase} in {area}. {description}",
        "Move to higher ground immediately. Avoid river crossings, low-lying roads and storm drains. Switch off electricity at the mains if water enters the property. Listen for instructions from NADMO and local authorities.",
    ),
    "rain": (
        "{severity} rainfall {urgency_phrase} in {area}. {description}",
        "Avoid flood-prone roads and low-lying areas. Park vehicles on high ground. Disconnect electronic devices during the storm. Monitor official channels for updates.",
    ),
    "storm": (
        "{severity} storm {urgency_phrase} in {area}. {description}",
        "Stay indoors and away from windows. Secure outdoor objects that could become projectiles. Avoid travel until the storm passes.",
    ),
    "fire": (
        "{severity} fire alert {urgency_phrase} in {area}. {description}",
        "Evacuate immediately if instructed. Avoid open flames and smoking. Report any fire to 112 or 192. Cover nose and mouth with a damp cloth in smoky areas.",
    ),
    "earthquake": (
        "{severity} earthquake {urgency_phrase} in {area}. {description}",
        "Drop, cover and hold on. Stay clear of windows and falling objects. Move to open ground after shaking stops. Expect aftershocks.",
    ),
    "default": (
        "{severity} alert {urgency_phrase} in {area}. {description}",
        "Follow guidance from NADMO and local authorities. Monitor official channels for updates.",
    ),
}


def _tool_draft_cap_advisory(event_type: str, severity: str, area: str, language: str = "en", description: str = "") -> dict:
    et_l = (event_type or "").lower()
    template_key = "default"
    for keyword in _ADVISORY_TEMPLATES:
        if keyword != "default" and keyword in et_l:
            template_key = keyword
            break
    headline_tpl, instruction = _ADVISORY_TEMPLATES[template_key]
    urgency_phrase = "expected" if severity in {"Moderate", "Minor"} else "imminent"
    headline = headline_tpl.format(
        severity=severity,
        urgency_phrase=urgency_phrase,
        area=area,
        description=description.strip() if description else "",
    ).strip()
    return {
        "language": language,
        "headline": headline[:140],
        "description": description or f"{severity} {event_type} situation reported in {area}. Follow guidance below.",
        "instruction": instruction,
    }


_TOOL_IMPLS = {
    "geocode_ghana_location": _tool_geocode_ghana_location,
    "lookup_population_density": _tool_lookup_population_density,
    "query_historical_alerts": _tool_query_historical_alerts,
    "assess_emergency_severity": _tool_assess_emergency_severity,
    "draft_cap_advisory": _tool_draft_cap_advisory,
}


# Function declarations for Gemma 4 / Gemini API. Schema mirrors OpenAPI; "type"
# values are JSON-schema strings (object, string, integer, number, array, boolean).
_FUNCTION_DECLARATIONS = [
    {
        "name": "geocode_ghana_location",
        "description": "Resolve a Ghanaian place name (city, town, neighbourhood, free-form description) to coordinates and admin boundaries. Always call this first to anchor the location before drafting the advisory.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Free-form location text, e.g., 'Osu in Accra' or 'Tamale'."}
            },
            "required": ["text"],
        },
    },
    {
        "name": "lookup_population_density",
        "description": "Return population, area, and density for a Ghana region. Use after geocoding to size the affected population.",
        "parameters": {
            "type": "object",
            "properties": {
                "region": {"type": "string", "description": "Region name as returned by geocode_ghana_location."},
                "district": {"type": "string", "description": "Optional district name."},
            },
            "required": ["region"],
        },
    },
    {
        "name": "query_historical_alerts",
        "description": "Look up recent alerts in MongoDB for a region and event type for context. Use before assessing severity.",
        "parameters": {
            "type": "object",
            "properties": {
                "region": {"type": "string", "description": "Region name to filter on (substring match against affected_regions)."},
                "event_type": {"type": "string", "description": "Optional event keyword (substring match)."},
                "limit": {"type": "integer", "description": "Max matches to return (default 5)."},
            },
            "required": ["region"],
        },
    },
    {
        "name": "assess_emergency_severity",
        "description": "Suggest CAP severity / urgency / certainty given the event type, affected population, and time of year.",
        "parameters": {
            "type": "object",
            "properties": {
                "event_type": {"type": "string"},
                "area_population": {"type": "integer", "description": "Optional. Population of the affected area (people)."},
                "time_of_year": {"type": "string", "description": "Optional. Ghana season label like 'rainy-major', 'dry-harmattan'."},
            },
            "required": ["event_type"],
        },
    },
    {
        "name": "draft_cap_advisory",
        "description": "Produce headline + description + instruction text from event_type / severity / area. Call this last, after geocoding and severity assessment, to assemble the final advisory text.",
        "parameters": {
            "type": "object",
            "properties": {
                "event_type": {"type": "string"},
                "severity": {"type": "string", "enum": ["Extreme", "Severe", "Moderate", "Minor", "Unknown"]},
                "area": {"type": "string", "description": "Human-readable area description, e.g., 'Osu, Greater Accra'."},
                "language": {"type": "string", "description": "ISO-639-1 code. Defaults to 'en'."},
                "description": {"type": "string", "description": "Optional descriptive text supplied by the user (verbatim)."},
            },
            "required": ["event_type", "severity", "area"],
        },
    },
]


def _build_system_instruction() -> str:
    """Single system-instruction string for Gemma 4. Includes the Ghana
    reference table inline so the model has the regions / known-places context
    without extra round-trips."""
    instructions = """You are an emergency-advisory drafting agent for the Ghana National CAP Platform.

You receive free-form text from a human responder describing a developing emergency in Ghana. Your job is to use the available tools to gather facts and then produce a CAP v1.2-conformant draft that the human will review and edit before dispatch.

Workflow you must follow on every request:
1. Call geocode_ghana_location to anchor the location described in the input.
2. If the geocode returns a region, call lookup_population_density and (optionally) query_historical_alerts to inform severity.
3. Call assess_emergency_severity with the event keyword + affected population + season hint to get suggested CAP severity / urgency / certainty.
4. Call draft_cap_advisory with the resolved event_type, severity, and area to produce the headline / description / instruction text.
5. Reply with a final assistant message that is ONLY a JSON object (no commentary, no code fences) matching this schema exactly:

{
  "headline": "string",
  "description": "string",
  "instruction": "string",
  "category": "Met|Geo|Safety|Health|Fire|Security|Rescue|Other",
  "event": "string",
  "urgency": "Immediate|Expected|Future|Past|Unknown",
  "severity": "Extreme|Severe|Moderate|Minor|Unknown",
  "certainty": "Observed|Likely|Possible|Unlikely|Unknown",
  "latitude": number,
  "longitude": number,
  "affected_region": "string",
  "affected_district": "string",
  "language": "en"
}

Rules:
- ALWAYS call the tools — do not guess coordinates or severity.
- Use category=Met for weather (rain, storm, drought, heat), Geo for geophysical (earthquake, landslide), Safety for general public-safety, Fire for fires, Health for disease/cholera, Security for civil unrest, Rescue for search/rescue.
- The final assistant message must be valid JSON, parseable with json.loads, and contain ONLY the JSON object."""

    reference = "\n\nGhana administrative regions and approximate population (2021 census):\n"
    for region, data in REGIONS.items():
        reference += f"- {region}: pop {data['population']:,}, {data['area_km2']:,} km², capital {data['capital']}\n"
    reference += "\nKnown places (subset; geocode tool covers more):\n"
    for name, place in PLACES.items():
        reference += f"- {name.title()}: {place['region']} / {place['district']} ({place['lat']:.4f}, {place['lng']:.4f})\n"

    return instructions + reference


class AdvisoryAgentService:
    """Runs the Gemma 4 tool-use loop for a single user input."""

    def __init__(self):
        self.client = None
        self._types = None
        if GEMINI_API_KEY:
            try:
                from google import genai
                from google.genai import types as gtypes
                self.client = genai.Client(api_key=GEMINI_API_KEY)
                self._types = gtypes
                logger.info("Advisory agent initialised (model=%s, provider=Gemini API).", GEMINI_MODEL)
            except Exception as e:
                logger.warning("google-genai client init failed: %s. Agent will mock.", e)
        else:
            logger.info("GEMINI_API_KEY not set — advisory agent will mock.")

    def draft_cap(self, user_text: str) -> dict:
        if not user_text or not user_text.strip():
            return {"error": "empty_input"}

        if not self.client:
            return self._mock_response(user_text)

        try:
            return self._run_loop(user_text)
        except Exception as e:
            logger.error("Advisory agent failed: %s", e)
            return self._mock_response(user_text, error=str(e))

    def _run_loop(self, user_text: str) -> dict:
        types = self._types
        # Gemini API "Content" stack: a list of {role, parts} with parts being
        # text / function_call / function_response.
        contents: list[Any] = [
            types.Content(role="user", parts=[types.Part.from_text(text=user_text)])
        ]
        config = types.GenerateContentConfig(
            tools=[types.Tool(function_declarations=_FUNCTION_DECLARATIONS)],
            system_instruction=_build_system_instruction(),
        )
        tool_call_log: list[dict] = []

        for turn in range(MAX_AGENT_TURNS):
            response = self.client.models.generate_content(
                model=GEMINI_MODEL,
                contents=contents,
                config=config,
            )

            # Append the model's full response Content to maintain conversation
            # state (this preserves the function_call ids the API expects to
            # match against the function_response we send back).
            candidate = response.candidates[0] if response.candidates else None
            if candidate is None or candidate.content is None:
                return {"error": "agent_returned_empty", "tool_calls": tool_call_log}
            contents.append(candidate.content)

            function_calls = response.function_calls or []
            if not function_calls:
                # Final response — extract text and parse as JSON.
                text = (response.text or "").strip()
                parsed = self._extract_json(text)
                if parsed is None:
                    return {"error": "agent_returned_non_json", "raw": text[:500], "tool_calls": tool_call_log}
                parsed.setdefault("agent", {})
                parsed["agent"]["tool_calls"] = tool_call_log
                parsed["agent"]["model"] = GEMINI_MODEL
                parsed["agent"]["turns"] = turn + 1
                parsed["agent"]["mock"] = False
                return parsed

            # Execute every tool call, build function_response parts, send back.
            response_parts = []
            for fc in function_calls:
                name = fc.name
                args = dict(fc.args or {})
                impl = _TOOL_IMPLS.get(name)
                if not impl:
                    output = {"error": f"unknown_tool: {name}"}
                else:
                    try:
                        output = impl(**args)
                    except TypeError as e:
                        output = {"error": f"bad_args: {e}"}
                    except Exception as e:
                        logger.warning("Tool %s raised: %s", name, e)
                        output = {"error": f"tool_failed: {e}"}
                tool_call_log.append({"tool": name, "args": args, "output": output})
                response_parts.append(
                    types.Part.from_function_response(name=name, response=output)
                )
            contents.append(types.Content(role="user", parts=response_parts))

        return {"error": "max_turns_exceeded", "tool_calls": tool_call_log}

    @staticmethod
    def _extract_json(text: str) -> dict | None:
        if not text:
            return None
        candidate = text.strip()
        if candidate.startswith("```"):
            candidate = candidate.strip("`")
            if candidate.lower().startswith("json"):
                candidate = candidate[4:]
            candidate = candidate.strip()
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            # Tolerate stray prose around the object — extract the outermost {...}.
            start = candidate.find("{")
            end = candidate.rfind("}")
            if start >= 0 and end > start:
                try:
                    return json.loads(candidate[start:end + 1])
                except json.JSONDecodeError:
                    return None
            return None

    @staticmethod
    def _mock_response(user_text: str, error: str | None = None) -> dict:
        place = lookup_place(user_text) or {}
        lat = place.get("lat", 5.6037)
        lng = place.get("lng", -0.1870)
        region = place.get("region", "Greater Accra")
        district = place.get("district", "Accra Metropolitan")

        event = "Weather Alert"
        for keyword in ("rain", "flood", "storm", "fire", "earthquake", "cholera", "drought"):
            if keyword in user_text.lower():
                event = keyword.title()
                break

        return {
            "headline": f"[MOCK] {event} alert for {place.get('name', 'unknown area').title()}",
            "description": f"[MOCK draft — set GEMINI_API_KEY for the real agent] {user_text}",
            "instruction": "[MOCK] Real instructions will populate when GEMINI_API_KEY is configured.",
            "category": "Met" if event.lower() in {"rain", "flood", "storm", "drought"} else "Other",
            "event": event,
            "urgency": "Expected",
            "severity": "Moderate",
            "certainty": "Likely",
            "latitude": lat,
            "longitude": lng,
            "affected_region": region,
            "affected_district": district,
            "language": "en",
            "agent": {
                "mock": True,
                "reason": error or "GEMINI_API_KEY not set",
                "tool_calls": [],
                "model": None,
                "turns": 0,
            },
        }


advisory_agent_service = AdvisoryAgentService()
