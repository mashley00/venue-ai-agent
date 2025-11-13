import os
import requests
from typing import Any, Dict, List

from app.services.geo import geocode, haversine_miles

API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

# We still bias discovery toward these query concepts,
# but we will NOT use them as the final category label.
QUERY_BASES = [
    "library",
    "community college",
    "technical school",
    "senior center",
    "community center",
]


def _meters(mi: int) -> int:
    return int(mi * 1609.34)


def _educationality_from_types(types: List[str]) -> float:
    """
    Derive a rough "educationality" score from Google place types.

    This is intentionally conservative: we never force something
    to be treated like a library unless Google actually says so.
    """
    if not types:
        return 0.5

    tnorm = [t.lower() for t in types]

    if any("library" in t for t in tnorm):
        return 1.0

    # College / university
    if any("university" in t or "college" in t for t in tnorm):
        return 0.9

    # Schools / academies / technical schools
    if any(
        "school" in t
        or "academy" in t
        or "polytechnic" in t
        or "technical" in t
        for t in tnorm
    ):
        return 0.85

    # Community / civic centers
    if any(
        "community_center" in t
        or "community_centre" in t
        or "civic_center" in t
        or "civic_centre" in t
        or "town_hall" in t
        for t in tnorm
    ):
        return 0.6

    # Places of worship are often usable but not ideal for all topics
    if any("church" in t or "place_of_worship" in t for t in tnorm):
        return 0.7

    # Everything else defaults to neutral-ish
    return 0.5


def discover(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Google Places Text Search with explicit location+radius.

    - Uses QUERY_BASES (library, community college, etc.) to find candidates.
    - For each result, we:
        * compute distance via haversine
        * HARD-FILTER by radius (miles)
        * keep Google's own `types` list
        * set `category` from the primary type (NOT from our query)
        * derive an educationality score from the types
    """
    if not API_KEY:
        return []

    cities = payload.get("cities") or []
    zips = payload.get("zips") or []
    radius_miles = int(payload.get("radius_miles", 6))
    radius = _meters(radius_miles)

    # We either search by explicit cities or by ZIPs as free-form anchors
    targets = cities if cities else zips
    out: List[Dict[str, Any]] = []

    for target in targets:
        anchor = geocode(target)
        if not anchor:
            continue

        lat, lng = anchor["lat"], anchor["lng"]

        for q in QUERY_BASES:
            url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
            params = {
                "query": q,
                "location": f"{lat},{lng}",
                "radius": radius,
                "key": API_KEY,
            }
            try:
                r = requests.get(url, params=params, timeout=10)
                r.raise_for_status()
                data = r.json()
            except Exception as e:
                print(f"[places] error {e}")
                continue

            for item in data.get("results", []):
                geo = item.get("geometry", {}).get("location", {})
                vlat = geo.get("lat")
                vlng = geo.get("lng")
                dist = None
                if vlat is not None and vlng is not None:
                    dist = haversine_miles(lat, lng, vlat, vlng)

                # HARD FILTER: must be within radius_miles
                if dist is None or dist > radius_miles:
                    continue

                # Use Google's own place types for classification
                types = item.get("types") or []
                if not isinstance(types, list):
                    types = []

                primary_type = types[0] if types else None

                # IMPORTANT: category is based on Google's types,
                # NOT on the query (q).
                category = primary_type

                educationality = _educationality_from_types(types)

                out.append(
                    {
                        "name": item.get("name"),
                        "address": item.get("formatted_address"),
                        "place_id": item.get("place_id"),
                        "lat": vlat,
                        "lng": vlng,
                        "city": target,
                        "category": category,          # what Google thinks it is
                        "types": types,                # full type list from Google
                        "query_category": q,           # which search query found it
                        "website_url": None,
                        "phone": None,
                        "availability_status": "unknown",
                        "educationality": educationality,
                        "distance_miles": round(dist, 2) if dist is not None else None,
                        "source": "google",
                    }
                )

    return out




