from typing import List, Dict, Any

from fastapi import APIRouter

from app.schemas.rank import RankPreviewPayload, RankPreviewResult
from app.services import places, merge, extract, scoring

router = APIRouter()


# --- Helper utilities -----------------------------------------------------


EXCLUDED_KEYWORDS: List[str] = [
    # senior / long-term care
    "assisted living",
    "independent living",
    "senior living",
    "senior apartments",
    "senior apartment",
    "retirement community",
    "memory care",
    "nursing home",
    "rehabilitation center",
    "rehab center",
    "skilled nursing",
    "post acute",
    "post-acute",
    # housing / residential
    "apartments",
    "apartment",
    "condominium",
    "condominiums",
    "condo",
    "condos",
    # neighborhood / hoa
    "homeowners association",
    "hoa",
    "neighborhood association",
    "civic association",
    # misc clearly non-venues
    "funeral home",
    "mortuary",
    "cemetery",
    "little free library",
    "free little library",
]


def _attr(payload: Any, *names: str, default=None):
    """
    Safely read a field from the payload, trying several possible names so
    we don't depend on the exact Pydantic schema.
    """
    for name in names:
        if hasattr(payload, name):
            return getattr(payload, name)
    return default


def normalize_zip_list(raw) -> List[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        zips = raw
    else:
        zips = str(raw).split(",")
    return [z.strip() for z in zips if z and z.strip()]


def is_irrelevant_venue(candidate: Dict[str, Any]) -> bool:
    """
    Drop obviously bad venue types based on name / category keywords.
    This is intentionally conservative – we only filter when we're very sure.
    """
    name = (candidate.get("name") or "").lower()
    # common fields that might hold types / categories
    categories = candidate.get("types") or candidate.get("categories") or []
    if isinstance(categories, list):
        cat_text = " ".join(str(c) for c in categories).lower()
    else:
        cat_text = str(categories).lower()

    haystack = f"{name} {cat_text}"

    for kw in EXCLUDED_KEYWORDS:
        if kw in haystack:
            return True

    return False


def matches_geography(candidate: Dict[str, Any], payload: Any) -> bool:
    """
    Best-effort geo filter using whatever address info we have on the candidate.
    We *don't* assume a particular shape of the candidate or payload.
    """
    city = (_attr(payload, "city", "City", default="") or "").strip().lower()
    state = (_attr(payload, "state", "State", default="") or "").strip().lower()
    zip_raw = _attr(payload, "zip_codes", "zipcodes", "zips", "postal_codes", default=[])
    zip_list = normalize_zip_list(zip_raw)

    # Build a single address string from all plausible fields on the candidate.
    addr_bits: List[str] = []
    for key in ("formatted_address", "address", "vicinity", "city", "state", "postal_code", "zipcode", "zip"):
        val = candidate.get(key)
        if val:
            addr_bits.append(str(val))
    address = " ".join(addr_bits).lower()

    # If we have zip codes, require at least one to appear in the address.
    if zip_list:
        if not any(z.lower() in address for z in zip_list):
            # allow a fallback where we still keep it if city+state both match
            pass_zip = False
        else:
            pass_zip = True
    else:
        pass_zip = True  # no zip constraint

    # city + state checks (only applied when present in payload)
    city_ok = True
    if city:
        city_ok = city in address

    state_ok = True
    if state:
        state_ok = state in address

    # Require state to match when provided.
    if state and not state_ok:
        return False

    # If we have zips, we want (zip OR (city+state))
    if zip_list:
        return pass_zip or (city_ok and state_ok)

    # No zips – fall back to city+state when available.
    if city and state:
        return city_ok and state_ok
    if city:
        return city_ok
    if state:
        return state_ok

    # If we truly know nothing, don't filter it out here.
    return True


# --- API endpoints --------------------------------------------------------


@router.post("/rank/preview", response_model=RankPreviewResult)
def preview(payload: RankPreviewPayload) -> RankPreviewResult:
    """
    Preview rank and candidate venues.

    Flow:
    1. Discover candidates from Google Places (and optionally Yelp later).
    2. Merge / dedupe with existing merge service.
    3. Apply geo-radius and keyword filters to drop irrelevant venues.
    4. Enrich + score remaining candidates.
    """
    # 1) Discover from Google
    google_list = places.discover(payload)

    # 2) Merge candidates – we currently don't use Yelp; pass an empty list
    #    to satisfy the merge_candidates signature (google_list, yelp_list).
    merged: List[Dict[str, Any]] = merge.merge_candidates(google_list, [])

    # 3) Apply geo + relevance filters
    filtered: List[Dict[str, Any]] = []
    for cand in merged:
        if not matches_geography(cand, payload):
            continue
        if is_irrelevant_venue(cand):
            continue
        filtered.append(cand)

    # 4) Enrich & score
    enriched = [extract.enrich(v) for v in filtered]
    sorted_scores = scoring.rank(enriched)

    return RankPreviewResult(
        results=sorted_scores,
        candidates=enriched,
    )


