import re
from typing import List, Dict, Tuple

def _norm(s: str) -> str:
    if not s: return ""
    s = s.lower()
    s = re.sub(r"[\.\,\-\(\)\'\"\&/]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    # drop common suffixes
    s = re.sub(r"\b(inc|llc|co|corp|the|center|centre)\b", "", s)
    return re.sub(r"\s+", " ", s).strip()

def _key(v: dict) -> Tuple[str, str]:
    return (_norm(v.get("name","")), _norm(v.get("city","")))

def merge_candidates(google_list: List[dict], yelp_list: List[dict]) -> List[dict]:
    """
    Simple, fast de-dupe by (normalized name, city).
    Prefer entries with Google place_id. Merge phone/website/rating.
    """
    merged: Dict[Tuple[str,str], dict] = {}

    def _merge(a: dict, b: dict) -> dict:
        out = dict(a)
        for k in ["address","website_url","booking_url","phone","availability_status","educationality","distance_miles"]:
            out[k] = out.get(k) or b.get(k)
        # preserve IDs/sources
        for k in ["place_id","yelp_id","source"]:
            out[k] = out.get(k) or b.get(k)
        # take better rating if present
        if b.get("yelp_rating"):
            out["yelp_rating"] = b.get("yelp_rating")
            out["yelp_review_count"] = b.get("yelp_review_count")
        return out

    # seed with Google first
    for g in google_list:
        merged[_key(g)] = g

    # fold in Yelp
    for y in yelp_list:
        k = _key(y)
        if k in merged:
            merged[k] = _merge(merged[k], y)
        else:
            merged[k] = y

    # rank-friendly array
    out = list(merged.values())
    return out
