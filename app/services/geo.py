import math, os, requests

GOOGLE_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

def geocode(target: str):
    """
    Return {'lat': float, 'lng': float, 'locality': str | None, 'postal_code': str | None}
    Uses Google PLACES Text Search instead of the Geocoding API so we only need one API enabled.
    """
    if not GOOGLE_KEY or not target:
        return None

    # Use Places Text Search to find a central point for the city or ZIP
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    try:
        r = requests.get(url, params={"query": target, "key": GOOGLE_KEY}, timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception:
        return None

    results = data.get("results") or []
    if not results:
        return None

    first = results[0]
    loc = first.get("geometry", {}).get("location", {})
    lat = loc.get("lat")
    lng = loc.get("lng")
    if lat is None or lng is None:
        return None

    # Text Search doesn't always give full address_components; we don't need them right now
    return {
        "lat": lat,
        "lng": lng,
        "locality": None,
        "postal_code": None,
    }

def haversine_miles(lat1, lon1, lat2, lon2):
    R = 3958.7613
    p = math.pi / 180.0
    a = (
        0.5 - math.cos((lat2 - lat1) * p) / 2
        + math.cos(lat1 * p) * math.cos(lat2 * p) * (1 - math.cos((lon2 - lon1) * p)) / 2
    )
    return 2 * R * math.asin(math.sqrt(a))

