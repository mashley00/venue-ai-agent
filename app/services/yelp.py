import os, requests
from app.services.geo import geocode, haversine_miles

API_KEY = os.getenv("YELP_API_KEY")
BASE = "https://api.yelp.com/v3/businesses/search"
HEADERS = {"Authorization": f"Bearer {API_KEY}"} if API_KEY else {}

# Keep Yelp categories narrow to educational/neutral
CATEGORIES = [
    "libraries",
    "collegeuniv",
    "adultedu",
    "education",
    "communitycenters",
    "seniorcenters",
]

def _meters(mi: int) -> int:
    return int(mi * 1609.34)

def discover(payload: dict):
    if not API_KEY:
        return []

    cities = payload.get("cities") or []
    zips = payload.get("zips") or []
    radius_miles = int(payload.get("radius_miles", 6))
    radius = min(_meters(radius_miles), 40000)  # Yelp max 40km

    targets = cities if cities else zips
    out = []

    for target in targets:
        anchor = geocode(target)
        if not anchor:
            continue
        alat, alng = anchor["lat"], anchor["lng"]

        for cat in CATEGORIES:
            params = {
                "latitude": alat,
                "longitude": alng,
                "categories": cat,
                "radius": radius,
                "limit": 50,
                "sort_by": "best_match",
            }
            try:
                r = requests.get(BASE, headers=HEADERS, params=params, timeout=10)
                r.raise_for_status()
                data = r.json()
            except Exception as e:
                print(f"[yelp] error {e}")
                continue

            for b in data.get("businesses", []):
                coords = b.get("coordinates") or {}
                vlat, vlng = coords.get("latitude"), coords.get("longitude")
                dist = None
                if vlat is not None and vlng is not None:
                    dist = haversine_miles(alat, alng, vlat, vlng)

                # HARD FILTER again (belt-and-suspenders)
                if dist is None or dist > radius_miles:
                    continue

                addr = ", ".join(b.get("location", {}).get("display_address", [])).strip() or None
                phone = b.get("display_phone") or b.get("phone")
                out.append({
                    "name": b.get("name"),
                    "address": addr,
                    "yelp_id": b.get("id"),
                    "lat": vlat, "lng": vlng,
                    "city": target,
                    "category": cat,
                    "website_url": b.get("url"),
                    "phone": phone,
                    "availability_status": "unknown",
                    "educationality": 0.9 if cat in ("libraries","collegeuniv","adultedu") else 0.7,
                    "distance_miles": round(dist, 2) if dist is not None else None,
                    "source": "yelp",
                })
    return out

