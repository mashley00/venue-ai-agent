import os, requests

API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

def discover(payload: dict):
    """Search Google Places API for educational venues."""
    cities = payload.get("cities") or []
    zips = payload.get("zips") or []
    radius = int(payload.get("radius_miles", 6)) * 1609
    attendees = payload.get("attendees", 30)

    query_bases = ["library", "community college", "technical school", "senior center", "community center"]
    results = []

    # Build location targets
    targets = cities if cities else zips
    for target in targets:
        for q in query_bases:
            query = f"{q} near {target}"
            url = (
                "https://maps.googleapis.com/maps/api/place/textsearch/json"
                f"?query={requests.utils.quote(query)}&radius={radius}&key={API_KEY}"
            )
            try:
                r = requests.get(url, timeout=10)
                r.raise_for_status()
                data = r.json()
            except Exception as e:
                print(f"[places] error {e}")
                continue

            for item in data.get("results", []):
                results.append({
                    "name": item.get("name"),
                    "address": item.get("formatted_address"),
                    "place_id": item.get("place_id"),
                    "city": target,
                    "category": q,
                    "website_url": None,
                    "phone": None,
                    "availability_status": "unknown",
                    "educationality": 1.0 if "library" in q else 0.8,
                    "distance_miles": None,
                })
    return results

