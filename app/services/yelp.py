import os, requests, math

API_KEY = os.getenv("YELP_API_KEY")
BASE = "https://api.yelp.com/v3/businesses/search"

HEADERS = {"Authorization": f"Bearer {API_KEY}"} if API_KEY else {}

# Yelp categories approximating our targets
CATEGORIES = [
    "libraries",
    "collegeuniv",
    "adultedu",
    "education",
    "communitycenters",
    "seniorcenters",
    "venues",  # sometimes used for event venues
]

def _meters(miles: int) -> int:
    return int(miles * 1609.34)

def discover(payload: dict):
    """
    Returns a list of normalized venue dicts from Yelp Fusion.
    If YELP_API_KEY is missing, returns [] so Google results still work.
    """
    if not API_KEY:
        return []

    cities = payload.get("cities") or []
    zips = payload.get("zips") or []
    radius_miles = int(payload.get("radius_miles", 6))
    radius = min(_meters(radius_miles), 40000)  # Yelp max 40km

    targets = cities if cities else zips
    results = []

    for target in targets:
        for cat in CATEGORIES:
            params = {
                "location": target,
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
                addr = ", ".join(b.get("location", {}).get("display_address", [])).strip() or None
                phone = b.get("display_phone") or b.get("phone")
                results.append({
                    "name": b.get("name"),
                    "address": addr,
                    "yelp_id": b.get("id"),
                    "city": target,
                    "category": cat,
                    "website_url": b.get("url"),
                    "phone": phone,
                    "availability_status": "unknown",
                    "educationality": 0.9 if cat in ("libraries","collegeuniv","adultedu") else 0.6,
                    "distance_miles": (b.get("distance", None) or 0) / 1609.34 if b.get("distance") else None,
                    "yelp_rating": b.get("rating"),
                    "yelp_review_count": b.get("review_count"),
                    "source": "yelp",
                })
    return results
