import os, random

# NOTE: This is a mocked discovery function for MVP.
# Replace with real Google Places Text/Nearby Search + Place Details calls.
# Keep logic identical: return a list of normalized dicts.

def discover(payload: dict) -> list[dict]:
    cities = payload.get("cities", [])
    zips = payload.get("zips", [])
    radius = payload.get("radius_miles", 6)

    samples = []
    for city in cities or ["Sample City"]:
        samples += [
            {
                "name": f"{city} Public Library",
                "category": "library",
                "educationality": 1.0,
                "address": f"123 Main St, {city}",
                "city": city,
                "state": "",
                "zip": zips[0] if zips else "",
                "distance_miles": round(random.uniform(0.5, radius), 1),
                "website_url": "https://example.org/library",
                "booking_url": "https://example.org/library/rooms",
                "phone": "(555) 123-4567",
                "amenities": {
                    "projector": True, "screen_tv": True, "wifi": True, "tables_chairs": True
                },
                "availability_status": "unknown",
                "availability_source": None
            },
            {
                "name": f"{city} Community College – Continuing Ed",
                "category": "community_college",
                "educationality": 0.9,
                "address": f"45 College Ave, {city}",
                "city": city,
                "state": "",
                "zip": zips[0] if zips else "",
                "distance_miles": round(random.uniform(1.0, radius), 1),
                "website_url": "https://example.edu/venue",
                "booking_url": None,
                "phone": "(555) 222-9090",
                "amenities": {
                    "projector": True, "screen_tv": True, "wifi": True, "tables_chairs": True
                },
                "availability_status": "unknown",
                "availability_source": None
            },
            {
                "name": f"{city} Hotel & Conference Center",
                "category": "hotel_conference",
                "educationality": 0.4,
                "address": f"9 Center Blvd, {city}",
                "city": city,
                "state": "",
                "zip": zips[0] if zips else "",
                "distance_miles": round(random.uniform(0.8, radius), 1),
                "website_url": "https://example.com/hotel",
                "booking_url": "https://example.com/hotel/meetings",
                "phone": "(555) 333-7777",
                "amenities": {"projector": True, "screen_tv": True, "wifi": True, "tables_chairs": True},
                "availability_status": "unknown",
                "availability_source": None
            }
        ]
    return samples
