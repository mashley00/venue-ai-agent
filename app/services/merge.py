import re
from typing import List, Dict, Tuple

def _norm(s: str) -> str:
    if not s: return ""
    s = s.lower()
    s = re.sub(r"[\.\,\-\(\)\'\"\&/]", " ", s)
    s = re.sub(r"\b(inc|llc|co|corp|the|center|centre|community)\b", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _coord_bucket(v: dict) -> str:
    # bucket lat/lng to ~30m grid to coalesce close duplicates
    lat, lng = v.get("lat"), v.get("lng")
    if lat is None or lng is None:
        return ""
    return f"{round(lat, 4)}:{round(lng, 4)}"

def _key(v: dict) -> Tuple[str, str]:
    name = _norm(v.get("name",""))
    addr = _norm(v.get("address",""))
    if addr:
        return (name, addr)
    # fall back to coord bucket, then city
    cb = _coord_bucket(v)
    if cb:
        return (name, cb)
    return (name, _norm(v.get("city","")))

def merge_candidates(google_list: List[dict], yelp_list: List[dict]) -> List[dict]:
    merged: Dict[Tuple[str,str], dict] = {}

    def _merge(a: dict, b: dict) -> dict:
        out = dict(a)
        # Prefer Google’s IDs if present
        for k in ["place_id","yelp_id","lat","lng","source"]:
            out[k] = out.get(k) or b.get(k)
        # Fill blanks from b
        for k in ["address","website_url","booking_url","phone","availability_status","educationality","distance_miles","category"]:
            out[k] = out.get(k) or b.get(k)
        # Keep shorter distance if available
        if out.get("distance_miles") is None and b.get("distance_miles") is not None:
            out["distance_miles"] = b["distance_miles"]
        elif out.get("distance_miles") is not None and b.get("distance_miles") is not None:
            out["distance_miles"] = min(out["distance_miles"], b["distance_miles"])
        return out

    for g in google_list:
        merged[_key(g)] = g

    for y in yelp_list:
        k = _key(y)
        if k in merged:
            merged[k] = _merge(merged[k], y)
        else:
            merged[k] = y

    return list(merged.values())

