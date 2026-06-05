"""Static Ghana reference data used by the AI advisory agent's tools.

Sources / approximate values:
- Population: Ghana Statistical Service 2021 Population & Housing Census.
- Area: GSS region-area summaries.
- Place coordinates: OSM-derived approximations for major cities and the
  best-known Accra neighbourhoods. Refine via Nominatim or a richer dataset
  in a follow-up phase if the demo set proves insufficient.

The structure is intentionally compact and human-editable — extend in place
rather than building a full gazetteer. The agent's geocode tool falls back
to OpenStreetMap Nominatim for places not in this table.
"""

# ──────────────────────────── Regions (admin-1) ────────────────────────────

# Population per region from GSS 2021 census; area in km².
REGIONS: dict[str, dict] = {
    "Greater Accra": {"population": 5_455_692, "area_km2": 3_245, "capital": "Accra"},
    "Ashanti": {"population": 5_440_463, "area_km2": 24_389, "capital": "Kumasi"},
    "Eastern": {"population": 2_925_653, "area_km2": 19_323, "capital": "Koforidua"},
    "Western": {"population": 2_060_585, "area_km2": 13_842, "capital": "Sekondi-Takoradi"},
    "Central": {"population": 2_859_821, "area_km2": 9_826, "capital": "Cape Coast"},
    "Volta": {"population": 1_649_523, "area_km2": 13_733, "capital": "Ho"},
    "Northern": {"population": 2_310_939, "area_km2": 26_558, "capital": "Tamale"},
    "Upper East": {"population": 1_301_221, "area_km2": 8_842, "capital": "Bolgatanga"},
    "Upper West": {"population": 901_502, "area_km2": 18_476, "capital": "Wa"},
    "Bono": {"population": 1_208_649, "area_km2": 11_103, "capital": "Sunyani"},
    "Bono East": {"population": 1_203_400, "area_km2": 23_248, "capital": "Techiman"},
    "Ahafo": {"population": 564_668, "area_km2": 5_193, "capital": "Goaso"},
    "Western North": {"population": 880_921, "area_km2": 10_074, "capital": "Sefwi Wiawso"},
    "Oti": {"population": 747_256, "area_km2": 11_097, "capital": "Dambai"},
    "Savannah": {"population": 653_266, "area_km2": 35_862, "capital": "Damongo"},
    "North East": {"population": 658_946, "area_km2": 8_722, "capital": "Nalerigu"},
}


def region_density(region: str) -> float | None:
    """Population density (people per km²) for a region, or None if unknown."""
    data = REGIONS.get(region)
    if not data or not data.get("area_km2"):
        return None
    return round(data["population"] / data["area_km2"], 1)


# ─────────────────────────── Places (lookup table) ─────────────────────────

# Lowercase keys for lookup; values describe the canonical place.
# Type: 'city', 'neighborhood', 'town'.
PLACES: dict[str, dict] = {
    # Cities (regional capitals + major towns)
    "accra":            {"lat": 5.6037, "lng": -0.1870, "region": "Greater Accra", "district": "Accra Metropolitan", "type": "city"},
    "kumasi":           {"lat": 6.6885, "lng": -1.6244, "region": "Ashanti", "district": "Kumasi Metropolitan", "type": "city"},
    "tamale":           {"lat": 9.4008, "lng": -0.8393, "region": "Northern", "district": "Tamale Metropolitan", "type": "city"},
    "cape coast":       {"lat": 5.1054, "lng": -1.2466, "region": "Central", "district": "Cape Coast Metropolitan", "type": "city"},
    "sekondi-takoradi": {"lat": 4.9347, "lng": -1.7079, "region": "Western", "district": "Sekondi-Takoradi Metropolitan", "type": "city"},
    "takoradi":         {"lat": 4.8898, "lng": -1.7556, "region": "Western", "district": "Sekondi-Takoradi Metropolitan", "type": "city"},
    "tema":             {"lat": 5.6698, "lng": 0.0166, "region": "Greater Accra", "district": "Tema Metropolitan", "type": "city"},
    "sunyani":          {"lat": 7.3349, "lng": -2.3265, "region": "Bono", "district": "Sunyani Municipal", "type": "city"},
    "ho":               {"lat": 6.6111, "lng": 0.4708, "region": "Volta", "district": "Ho Municipal", "type": "city"},
    "bolgatanga":       {"lat": 10.7853, "lng": -0.8512, "region": "Upper East", "district": "Bolgatanga Municipal", "type": "city"},
    "wa":               {"lat": 10.0606, "lng": -2.5057, "region": "Upper West", "district": "Wa Municipal", "type": "city"},
    "koforidua":        {"lat": 6.0892, "lng": -0.2596, "region": "Eastern", "district": "New Juaben South Municipal", "type": "city"},
    "techiman":         {"lat": 7.5867, "lng": -1.9388, "region": "Bono East", "district": "Techiman Municipal", "type": "city"},
    "obuasi":           {"lat": 6.2027, "lng": -1.6661, "region": "Ashanti", "district": "Obuasi Municipal", "type": "town"},
    "tarkwa":           {"lat": 5.3041, "lng": -1.9925, "region": "Western", "district": "Tarkwa-Nsuaem Municipal", "type": "town"},
    "aflao":            {"lat": 6.1183, "lng": 1.1836, "region": "Volta", "district": "Ketu South Municipal", "type": "town"},
    "yendi":            {"lat": 9.4422, "lng": -0.0095, "region": "Northern", "district": "Yendi Municipal", "type": "town"},
    "damongo":          {"lat": 9.0840, "lng": -1.8181, "region": "Savannah", "district": "West Gonja Municipal", "type": "town"},
    "nkawkaw":          {"lat": 6.5500, "lng": -0.7700, "region": "Eastern", "district": "Kwahu West Municipal", "type": "town"},
    "akosombo":         {"lat": 6.2667, "lng": 0.0500, "region": "Eastern", "district": "Asuogyaman", "type": "town"},
    "goaso":            {"lat": 6.8000, "lng": -2.5167, "region": "Ahafo", "district": "Asunafo North Municipal", "type": "town"},

    # Accra neighbourhoods (most commonly referenced in the demo)
    "osu":              {"lat": 5.5567, "lng": -0.1820, "region": "Greater Accra", "district": "Accra Metropolitan", "type": "neighborhood"},
    "cantonments":      {"lat": 5.5784, "lng": -0.1685, "region": "Greater Accra", "district": "Accra Metropolitan", "type": "neighborhood"},
    "east legon":       {"lat": 5.6502, "lng": -0.1606, "region": "Greater Accra", "district": "Ayawaso West Municipal", "type": "neighborhood"},
    "labadi":           {"lat": 5.5663, "lng": -0.1502, "region": "Greater Accra", "district": "La Dade-Kotopon Municipal", "type": "neighborhood"},
    "la":               {"lat": 5.5663, "lng": -0.1502, "region": "Greater Accra", "district": "La Dade-Kotopon Municipal", "type": "neighborhood"},
    "adabraka":         {"lat": 5.5616, "lng": -0.2052, "region": "Greater Accra", "district": "Accra Metropolitan", "type": "neighborhood"},
    "madina":           {"lat": 5.6839, "lng": -0.1670, "region": "Greater Accra", "district": "La Nkwantanang-Madina Municipal", "type": "neighborhood"},
    "tesano":           {"lat": 5.5973, "lng": -0.2188, "region": "Greater Accra", "district": "Accra Metropolitan", "type": "neighborhood"},
    "achimota":         {"lat": 5.6195, "lng": -0.2278, "region": "Greater Accra", "district": "Ga East Municipal", "type": "neighborhood"},
    "spintex":          {"lat": 5.6164, "lng": -0.0833, "region": "Greater Accra", "district": "Ledzokuku Municipal", "type": "neighborhood"},
    "dansoman":         {"lat": 5.5394, "lng": -0.2536, "region": "Greater Accra", "district": "Ablekuma South Municipal", "type": "neighborhood"},
    "lapaz":            {"lat": 5.6094, "lng": -0.2564, "region": "Greater Accra", "district": "Okaikwei North Municipal", "type": "neighborhood"},
    "circle":           {"lat": 5.5685, "lng": -0.2080, "region": "Greater Accra", "district": "Accra Metropolitan", "type": "neighborhood"},
    "kasoa":            {"lat": 5.5340, "lng": -0.4170, "region": "Central", "district": "Awutu Senya East Municipal", "type": "town"},

    # Kumasi neighbourhoods
    "adum":             {"lat": 6.6928, "lng": -1.6244, "region": "Ashanti", "district": "Kumasi Metropolitan", "type": "neighborhood"},
    "ahodwo":           {"lat": 6.6738, "lng": -1.6364, "region": "Ashanti", "district": "Kumasi Metropolitan", "type": "neighborhood"},
    "asokwa":           {"lat": 6.6710, "lng": -1.6000, "region": "Ashanti", "district": "Asokwa Municipal", "type": "neighborhood"},

    # Additional Greater Accra neighbourhoods/towns — common alert locations
    # that previously fell through to Nominatim (which is blocked from cloud
    # egress IPs, e.g. Render), causing the geocode to 404. Static-first keeps
    # the area resolver working without an external call.
    "dzorwulu":         {"lat": 5.6126, "lng": -0.1969, "region": "Greater Accra", "district": "Ayawaso West Municipal", "type": "neighborhood"},
    "airport residential": {"lat": 5.6052, "lng": -0.1769, "region": "Greater Accra", "district": "Ayawaso West Municipal", "type": "neighborhood"},
    "ridge":            {"lat": 5.5650, "lng": -0.1960, "region": "Greater Accra", "district": "Accra Metropolitan", "type": "neighborhood"},
    "abelemkpe":        {"lat": 5.6010, "lng": -0.2110, "region": "Greater Accra", "district": "Ayawaso West Municipal", "type": "neighborhood"},
    "roman ridge":      {"lat": 5.5960, "lng": -0.2010, "region": "Greater Accra", "district": "Ayawaso West Municipal", "type": "neighborhood"},
    "kaneshie":         {"lat": 5.5640, "lng": -0.2330, "region": "Greater Accra", "district": "Accra Metropolitan", "type": "neighborhood"},
    "abeka":            {"lat": 5.5950, "lng": -0.2370, "region": "Greater Accra", "district": "Okaikwei North Municipal", "type": "neighborhood"},
    "dome":             {"lat": 5.6520, "lng": -0.2280, "region": "Greater Accra", "district": "Ga East Municipal", "type": "neighborhood"},
    "kwabenya":         {"lat": 5.6900, "lng": -0.2200, "region": "Greater Accra", "district": "Ga East Municipal", "type": "neighborhood"},
    "ashaiman":         {"lat": 5.6890, "lng": -0.0330, "region": "Greater Accra", "district": "Ashaiman Municipal", "type": "town"},
    "teshie":           {"lat": 5.5840, "lng": -0.1010, "region": "Greater Accra", "district": "Ledzokuku Municipal", "type": "neighborhood"},
    "nungua":           {"lat": 5.6010, "lng": -0.0730, "region": "Greater Accra", "district": "Krowor Municipal", "type": "neighborhood"},
    "sakumono":         {"lat": 5.6240, "lng": -0.0470, "region": "Greater Accra", "district": "Tema West Municipal", "type": "neighborhood"},
    "adenta":           {"lat": 5.7090, "lng": -0.1620, "region": "Greater Accra", "district": "Adentan Municipal", "type": "town"},
    "adentan":          {"lat": 5.7090, "lng": -0.1620, "region": "Greater Accra", "district": "Adentan Municipal", "type": "town"},
}


def lookup_place(text: str) -> dict | None:
    """Try to resolve free-form text against the static place table.

    Strategy (most specific match wins):
    1. Exact match on the whole lowercased input.
    2. Whole-word substring match prioritised by type:
       neighborhood > town > city. So 'Osu in Accra' returns Osu (neighborhood),
       not Accra (city). Within a tier, longest name wins so 'East Legon'
       beats a hypothetical 'Legon'.
    3. None → caller falls back to Nominatim.
    """
    if not text:
        return None
    raw = text.strip().lower()
    if raw in PLACES:
        return {"name": raw, **PLACES[raw]}

    import re
    type_priority = {"neighborhood": 0, "town": 1, "city": 2}

    best_name = None
    best_score = None  # tuple: (priority, -length); lower wins
    for name, place in PLACES.items():
        if not re.search(rf"\b{re.escape(name)}\b", raw):
            continue
        score = (type_priority.get(place.get("type"), 9), -len(name))
        if best_score is None or score < best_score:
            best_score = score
            best_name = name
    if best_name:
        return {"name": best_name, **PLACES[best_name]}
    return None


# ────────────────────────── Time-of-year heuristics ────────────────────────

# Ghana climate calendar (approximate, southern Ghana — northern is one season):
#   Major rainy season:  April – mid-July    (heavy rain, flood risk peaks May-Jun)
#   Minor rainy season:  September – November (less intense)
#   Dry season:          mid-July – August, December – March
#   Harmattan dust:      November – February (fire + respiratory hazard)
SEASON_BY_MONTH = {
    1: "dry-harmattan", 2: "dry-harmattan", 3: "dry",
    4: "rainy-major", 5: "rainy-major", 6: "rainy-major", 7: "rainy-major-tail",
    8: "dry-short", 9: "rainy-minor", 10: "rainy-minor", 11: "rainy-minor-tail",
    12: "dry-harmattan",
}


def current_season(month: int | None = None) -> str:
    """Return Ghana's broad seasonal label for the given month (1-12), or the
    current month if None. Useful for severity context (rain in May is more
    serious than rain in February)."""
    from datetime import datetime, timezone
    if month is None:
        month = datetime.now(timezone.utc).month
    return SEASON_BY_MONTH.get(month, "unknown")


# ─────────────────────── Region centroids + fallbacks ──────────────────────

# Geographic centre of Ghana — used as the last-resort fallback so the area
# resolver always returns a usable point instead of failing (404). Matches the
# default Leaflet view used by the live-events map.
GHANA_CENTROID = {"lat": 7.95, "lng": -1.02}

# Approximate centroid per region (regional capital coordinates). Lets the
# area resolver degrade to a region-level point when an exact place can't be
# geocoded — far better than a hard failure for the operator.
REGION_CENTROIDS: dict[str, dict] = {
    "Greater Accra": {"lat": 5.6037, "lng": -0.1870},
    "Ashanti":       {"lat": 6.6885, "lng": -1.6244},
    "Eastern":       {"lat": 6.0892, "lng": -0.2596},
    "Western":       {"lat": 4.9347, "lng": -1.7079},
    "Central":       {"lat": 5.1054, "lng": -1.2466},
    "Volta":         {"lat": 6.6111, "lng": 0.4708},
    "Northern":      {"lat": 9.4008, "lng": -0.8393},
    "Upper East":    {"lat": 10.7853, "lng": -0.8512},
    "Upper West":    {"lat": 10.0606, "lng": -2.5057},
    "Bono":          {"lat": 7.3349, "lng": -2.3265},
    "Bono East":     {"lat": 7.5867, "lng": -1.9388},
    "Ahafo":         {"lat": 6.8000, "lng": -2.5167},
    "Western North": {"lat": 6.2000, "lng": -2.4833},
    "Oti":           {"lat": 8.0667, "lng": 0.1833},
    "Savannah":      {"lat": 9.0840, "lng": -1.8181},
    "North East":    {"lat": 10.5333, "lng": -0.3667},
}


def region_centroid(region: str | None) -> dict | None:
    """Approximate {lat, lng} for a region name, or None if unknown."""
    if not region:
        return None
    return REGION_CENTROIDS.get(region)


def detect_region(text: str) -> str | None:
    """Best-effort region detection from free-form text. Used by the area
    resolver's graceful fallback when an exact place can't be geocoded.

    Strategy:
    1. Explicit region name in the text ("...in the Eastern Region", "Volta").
       Longest region name wins so "Upper East" beats a stray "East".
    2. A known place name in the text → that place's region (covers cases like
       "near Kumasi" where Kumasi is in PLACES with region=Ashanti).
    """
    if not text:
        return None
    import re
    raw = text.lower()

    best_region = None
    best_len = -1
    for region in REGIONS:
        if re.search(rf"\b{re.escape(region.lower())}\b", raw) and len(region) > best_len:
            best_region, best_len = region, len(region)
    if best_region:
        return best_region

    # Fall back to any known place mentioned in the text.
    hit = lookup_place(text)
    if hit and hit.get("region"):
        return hit["region"]
    return None
