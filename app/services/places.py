import os, requests
from app.services.geo import geocode, haversine_miles

API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

# Strict allow-list of educational/neutral venue types
QUERY_BASES = [
    "library",
    "community college",
    "technical school",
    "senior center",
    "community center",
]

def _meters(mi: int) -> int:
    return int(mi * 1609.34)

def discover(payload: dict):
    """
    Google Places Text Search with explicit location+radius.
    Then hard-filter by distance to ensure results are inside the radius.
    """
    if not API_KEY:
        return []

    cities = payload.get("cities") or []
    zips = payload.get("zips") or []
    radius_miles = int(payload.get("radius_miles", 6))
    radius = _meters(radius_miles)

    targets = cities if cities else zips
    out = []

    for target in targets:
        anchor = geocode(target)
        if not anchor:  # skip this target if we could not geocode
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
                vlat, vlng = geo.get("lat"), geo.get("lng")
                dist = None
                if vlat is not None and vlng is not None:
                    dist = haversine_miles(lat, lng, vlat, vlng)

                # HARD FILTER: must be within radius_miles
                if dist is None or dist > radius_miles:
                    continue

                out.append({
                    "name": item.get("name"),
                    "address": item.get("formatted_address"),
                    "place_id": item.get("place_id"),
                    "lat": vlat, "lng": vlng,
                    "city": target,
                    "category": q,
                    "website_url": None,
                    "phone": None,
                    "availability_status": "unknown",
                    "educationality": 1.0 if "library" in q else 0.85 if "college" in q or "technical" in q else 0.7,
                    "distance_miles": round(dist, 2) if dist is not None else None,
                    "source": "google",
                })
    return out


