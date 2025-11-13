from typing import List, Dict, Any, Iterable

from fastapi import APIRouter, Body

from app.services import places, merge, extract, scoring

router = APIRouter()

# ---------------------------------------------------------------------------
# Blocklist for clearly bad / non-seminar venues
# ---------------------------------------------------------------------------

EXCLUDED_KEYWORDS: List[str] = [
    # Residential care / senior living
    "assisted living",
    "independent living",
    "senior living",
    "senior center",
    "senior apartments",
    "senior apartment",
    "retirement community",
    "retirement village",
    "retirement home",
    "memory care",
    "alzheimers care",
    "alzheimer's care",
    "dementia care",
    "skilled nursing",
    "nursing home",
    "long-term care",
    "ltc facility",
    "continuing care",
    "ccrc",

    # Medical / rehab / health
    "post acute",
    "post-acute",
    "rehab center",
    "rehabilitation center",
    "rehabilitation hospital",
    "physical therapy",
    "outpatient rehab",
    "inpatient rehab",
    "hospital",
    "medical center",
    "surgery center",
    "surgical center",
    "dialysis center",
    "urgent care",
    "walk-in clinic",
    "walk in clinic",
    "emergency room",
    "trauma center",
    "hospice",
    "home health care",
    "home healthcare",
    "medical group",

    # Residential housing / apartments / condos
    "apartment",
    "apartments",
    "apartment community",
    "apartment homes",
    "apartment complex",
    "condominium",
    "condominiums",
    "condo",
    "condos",
    "condo association",
    "co-op",
    "co-op housing",
    "cooperative housing",
    "lofts",
    "student housing",
    "student apartments",
    "student residence",
    "dormitory",
    "residence hall",
    "mobile home park",
    "manufactured home community",
    "trailer park",

    # Neighborhood / HOA / property management
    "homeowners association",
    "hoa",
    "neighborhood association",
    "civic association",
    "residents association",
    "residential association",
    "property management",
    "apartment management",
    "condo management",

    # Tiny / non-venue locations
    "little free library",
    "free little library",
    "little library",
    "book box",

    # Purely residential / not public venues
    "townhomes",
    "townhome community",
    "townhouse community",
    "subdivision",
    "gated community",
    "residential community",
    "single-family homes",
    "single family homes",
    "residential apartments",

    # Childcare / K-12 (generally not your target)
    "daycare",
    "day care",
    "child care",
    "childcare",
    "preschool",
    "kindergarten",
    "elementary school",
    "primary school",
    "middle school",
    "junior high",
    "junior-high",
    "high school",
    "secondary school",

    # Death-care / obviously wrong
    "funeral home",
    "funeral service",
    "mortuary",
    "cremation",
    "cemetery",
]

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------


def _normalize_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def _normalize_zip_list(raw: Any) -> List[str]:
    if raw is None:
        return []

    items: List[str] = []

    if isinstance(raw, str):
        for part in raw.replace(";", ",").split(","):
            part = part.strip()
            if part:
                items.append(part)
    elif isinstance(raw, Iterable) and not isinstance(raw, (bytes, bytearray)):
        for v in raw:
            if v is None:
                continue
            s = str(v)
            for part in s.replace(";", ",").split(","):
                part = part.strip()
                if part:
                    items.append(part)
    else:
        items.append(str(raw).strip())

    zips: List[str] = []
    for val in items:
        if not val:
            continue
        if "-" in val and len(val) > 5:
            val = val.split("-", 1)[0]
        val = val.strip()
        if len(val) >= 3:
            zips.append(val.lower())
    return zips


def is_irrelevant_venue(candidate: Dict[str, Any]) -> bool:
    """
    Returns True if the candidate clearly represents a non-usable venue
    based on name/category/type keywords.
    """
    name = _normalize_str(candidate.get("name"))
    category = _normalize_str(candidate.get("category"))
    vtype = _normalize_str(candidate.get("type"))

    types = candidate.get("types") or candidate.get("categories") or []
    if isinstance(types, str):
        types_text = _normalize_str(types)
    else:
        types_text = " ".join(_normalize_str(t) for t in types)

    haystack = " ".join([name, category, vtype, types_text])

    for kw in EXCLUDED_KEYWORDS:
        if kw in haystack:
            return True

    return False


def matches_geography(candidate: Dict[str, Any], payload: Dict[str, Any]) -> bool:
    """
    Light textual geography check on top of the strict radius filter
    already applied inside app.services.places.discover.
    """
    city_q = _normalize_str(
        payload.get("city") or payload.get("City") or payload.get("locality")
    )
    state_q = _normalize_str(
        payload.get("state") or payload.get("State") or payload.get("state_code")
    )

    zip_raw = (
        payload.get("zip_codes")
        or payload.get("zipcodes")
        or payload.get("zips")
        or payload.get("postal_codes")
        or payload.get("zip")
        or payload.get("zipcode")
    )
    zips_q = _normalize_zip_list(zip_raw)

    addr_bits: List[str] = []
    for key in (
        "formatted_address",
        "address",
        "vicinity",
        "city",
        "locality",
        "state",
        "state_code",
        "region",
        "postal_code",
        "zipcode",
        "zip",
    ):
        val = candidate.get(key)
        if val:
            addr_bits.append(str(val))

    address = _normalize_str(" ".join(addr_bits))

    if state_q:
        if state_q not in address:
            return False

    if zips_q:
        zip_match = any(z in address for z in zips_q)
        if not zip_match:
            if city_q and city_q not in address:
                return False
    else:
        if city_q and city_q not in address:
            return False

    return True


# ---------------------------------------------------------------------------
# Router endpoint
# ---------------------------------------------------------------------------


@router.post("/preview")
def preview(payload: dict = Body(...)) -> Dict[str, Any]:
    """
    Preview ranked venue candidates.
    """
    if isinstance(payload, dict):
        payload_dict: Dict[str, Any] = payload
    else:
        try:
            payload_dict = dict(payload)  # type: ignore[arg-type]
        except Exception:
            payload_dict = {}

    # 1) Discover from Google with strict radius
    google_list = places.discover(payload_dict)

    # 2) Merge candidates – Yelp not wired yet
    merged = merge.merge_candidates(google_list, [])

    # 3) Apply geography + blocklist filters
    filtered: List[Dict[str, Any]] = []
    for cand in merged:
        if not matches_geography(cand, payload_dict):
            continue
        if is_irrelevant_venue(cand):
            continue
        filtered.append(cand)

    # 4) Enrich & score
    enriched: List[Dict[str, Any]] = []
    for v in filtered:
        v_enriched = extract.enrich(dict(v))
        try:
            total, reason, comps = scoring.score(v_enriched)
        except Exception:
            total, reason, comps = 0.0, "", {}

        v_enriched["score"] = total
        v_enriched["score_reason"] = reason

        # Normalize component names for the UI columns
        v_enriched["educationality"] = comps.get("educationality")
        v_enriched["availability_score"] = comps.get("availability")
        v_enriched["capacity_score"] = comps.get("capacity_fit")
        v_enriched["amenities_score"] = comps.get("amenities")
        v_enriched["logistics_score"] = comps.get("logistics")

        enriched.append(v_enriched)

    # 5) Sort by score descending
    enriched_sorted = sorted(
        enriched, key=lambda x: x.get("score", 0.0), reverse=True
    )

    # 6) Return plain dict (JSON)
    return {
        "results": enriched_sorted,
        "candidates": enriched_sorted,
    }


