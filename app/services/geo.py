import math, os, requests

GOOGLE_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

def geocode(target: str):
    """
    Return {'lat': float, 'lng': float, 'locality': str, 'postal_code': str}
    Uses Google Geocoding API.
    """
    if not GOOGLE_KEY or not target:
        return None
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    try:
        r = requests.get(url, params={"address": target, "key": GOOGLE_KEY}, timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception:
        return None
    if not data.get("results"):
        return None
    res = data["results"][0]
    loc = res["geometry"]["location"]
    comps = {c["types"][0]: c["long_name"] for c in res.get("address_components", []) if c.get("types")}
    # derive a good city/locality and postal_code if present
    locality = None
    for key in ("locality","postal_town","administrative_area_level_2"):
        if key in comps:
            locality = comps[key]
            break
    postal_code = comps.get("postal_code")
    return {"lat": loc["lat"], "lng": loc["lng"], "locality": locality, "postal_code": postal_code}

def haversine_miles(lat1, lon1, lat2, lon2):
    R = 3958.7613
    p = math.pi/180
    a = (0.5 - math.cos((lat2-lat1)*p)/2 +
         math.cos(lat1*p)*math.cos(lat2*p)*(1-math.cos((lon2-lon1)*p))/2)
    return 2*R*math.asin(math.sqrt(a))
