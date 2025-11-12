# Stub enrichment that would normally use Playwright to crawl the venue website
# For MVP we just pass through and ensure fields exist.

def enrich(v: dict) -> dict:
    v.setdefault("contact_name", None)
    v.setdefault("contact_email", None)
    v.setdefault("parking_notes", None)
    v.setdefault("disclosure_needed", False)
    v.setdefault("image_allowed", True)
    # Add sample room info if missing
    if "rooms" not in v:
        v["rooms"] = [
            {"room_name": "Main Meeting Room", "capacity_classroom": 24, "capacity_theater": 40, "fees_hour": 50.0, "fees_day": 300.0, "deposit": 0.0, "rental_policy_url": None}
        ]
    return v
