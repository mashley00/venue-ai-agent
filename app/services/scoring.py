EDU_WEIGHTS = {
    "library": 1.0,
    "community_college": 0.9,
    "tech_school": 0.85,
    "senior_center": 0.8,
    "community_center": 0.6,
    "hotel_conference": 0.4,
    "golf_banquet": 0.4
}

def _amenities_score(am: dict) -> float:
    if not am: 
        return 0.0
    keys = ["projector", "screen_tv", "wifi", "tables_chairs"]
    s = sum(1.0 for k in keys if am.get(k))
    return min(1.0, 0.25 * s)

def _capacity_fit(rooms: list, target_min=20, target_max=30) -> float:
    if not rooms:
        return 0.0
    best = 0.0
    for r in rooms:
        c_class = r.get("capacity_classroom") or 0
        c_theater = r.get("capacity_theater") or 0
        # Score 1.0 if classroom fits 20-30 OR theater >= 26
        score = 0.0
        if target_min <= c_class <= max(target_max, 30):
            score = max(score, 1.0)
        elif c_theater >= 26:
            score = max(score, 0.7)
        best = max(best, score)
    return best

def _availability_status_score(status: str | None) -> float:
    if status == "available":
        return 1.0
    if status == "maybe":
        return 0.6
    if status == "not_available":
        return 0.0
    return 0.5  # unknown

def _logistics_score(v: dict) -> float:
    # simple heuristic: parking notes exist → 0.8 else 0.6; distance under 6 → +0.2
    base = 0.6 + (0.2 if v.get("parking_notes") else 0.0)
    dist = v.get("distance_miles") or 999
    if dist <= 6:
        base += 0.2
    return min(1.0, base)

def score(v: dict):
    category = (v.get("category") or "").lower()
    edu = v.get("educationality")
    if edu is None or edu == 0.0:
        edu = EDU_WEIGHTS.get(category, 0.5)

    avail = _availability_status_score(v.get("availability_status"))
    am = _amenities_score(v.get("amenities") or {})
    cap = _capacity_fit(v.get("rooms") or [])
    log = _logistics_score(v)

    total = round(edu*0.35 + avail*0.25 + cap*0.20 + am*0.15 + log*0.05, 4)
    comps = {"educationality": edu, "availability": avail, "capacity_fit": cap, "amenities": am, "logistics": log}
    reason = f"Edu:{edu:.2f} Avail:{avail:.2f} Cap:{cap:.2f} Ams:{am:.2f} Log:{log:.2f}"
    return total, reason, comps
