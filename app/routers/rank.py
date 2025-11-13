from typing import List
from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from app.services import places, merge, anchors, extract, scoring

router = APIRouter(prefix="/rank", tags=["rank"])


# -----------------------
# Models
# -----------------------


class RankPayload(BaseModel):
    city: str = Field("", description="Primary city (for context only)")
    zips: List[str] = Field(default_factory=list, description="ZIP codes to anchor search")
    radius: float = Field(6.0, description="Search radius in miles")
    topic: str = Field("tir", description="Seminar topic code (TIR/EP/SS/etc.)")

    @classmethod
    def from_ui(cls, city: str, zips: str, miles: float, topic: str) -> "RankPayload":
        zips_list = [z.strip() for z in (zips or "").split(",") if z.strip()]
        return cls(
            city=city or "",
            zips=zips_list,
            radius=miles or 6.0,
            topic=(topic or "").lower(),
        )


# -----------------------
# Helpers – distance & filters
# -----------------------


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Simple haversine distance in statute miles."""
    from math import radians, sin, cos, asin, sqrt

    R = 3958.8  # Earth radius in miles
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return R * c


# Names we NEVER want as venues (case-insensitive, substring match)
EXCLUDED_NAME_KEYWORDS = [
    # senior / assisted living style housing
    "assisted living",
    "senior living",
    "senior apartments",
    "independent living",
    "memory care",
    "post acute",
    "post-acute",
    "rehab center",
    "rehabilitation center",
    "skilled nursing",
    "nursing home",
    "long term care",
    "ltc center",
    "home care",
    "hospice",
    # residential / apartment-style
    "apartments",
    "apartment homes",
    "apartment community",
    "condominiums",
    "condominium",
    "townhomes",
    # neighborhood / hoa
    "neighborhood association",
    "homeowners association",
    "hoa office",
    # misc clearly non-venue matches
    "little free library",
]


def _looks_irrelevant(venue: dict) -> bool:
    """Return True if the venue name clearly indicates a bad / unusable type."""
    name = (venue.get("name") or "").lower()
    if not name:
        return False
    return any(kw in name for kw in EXCLUDED_NAME_KEYWORDS)


def _final_radius_filter(
    cands: List[dict],
    geocoded_anchors: List[dict],
    radius_miles: float,
) -> List[dict]:
    """Attach distance_miles and drop venues outside the radius or obviously bad ones."""
    # Build a list of anchor (lat, lng) tuples from the geocoder
    anchors_xy = []
    for g in geocoded_anchors or []:
        if not g:
            continue
        lat = g.get("lat")
        lng = g.get("lng")
        if lat is None or lng is None:
            continue
        anchors_xy.append((lat, lng))

    # If we somehow have no anchors, just return the candidates unchanged
    if not anchors_xy:
        return cands

    filtered: List[dict] = []
    for v in cands:
        vlat = v.get("lat")
        vlng = v.get("lng")
        if vlat is None or vlng is None:
            # If we can't place it on a map, we can't use it for geo-based work
            continue

        # How far is this venue from the closest anchor?
        min_dist = min(
            haversine_miles(alat, alng, vlat, vlng) for (alat, alng) in anchors_xy
        )
        v["distance_miles"] = round(min_dist, 2)

        if min_dist > radius_miles:
            continue
        if _looks_irrelevant(v):
            continue

        filtered.append(v)

    return filtered


def _rank_inline(venues: List[dict]) -> List[dict]:
    ranked = []
    for v in venues:
        total, reason, comps = scoring.score(v)
        v["score_total"] = total
        v["reason_text"] = reason
        v["score_components"] = comps
        ranked.append(v)

    ranked.sort(key=lambda x: x.get("score_total", 0), reverse=True)
    for i, v in enumerate(ranked, start=1):
        v["rank"] = i
    return ranked


TABLE_COLUMNS = [
    ("rank", "Rank"),
    ("name", "Venue"),
    ("city", "City"),
    ("state", "State"),
    ("distance_miles", "Dist (mi)"),
    ("source", "Source"),
    ("phone", "Phone"),
    ("score_total", "Score"),
    ("reason_text", "Why it scored this way"),
    ("maps_url", "Maps / Website"),
]


def _to_html_table(ranked: List[dict]) -> str:
    rows = []
    for v in ranked:
        row = {col_key: v.get(col_key) for col_key, _ in TABLE_COLUMNS}
        if row.get("maps_url"):
            row["name"] = (
                f"<a href='{row['maps_url']}' target='_blank'>{row['name']}</a>"
            )
        rows.append(row)

    header_cells = "".join(f"<th>{label}</th>" for _, label in TABLE_COLUMNS)
    header = f"<tr>{header_cells}</tr>"

    body_rows = []
    for row in rows:
        cells = "".join(
            f"<td>{'' if v is None else v}</td>"
            for key, _ in TABLE_COLUMNS
            for v in [row.get(key)]
        )
        body_rows.append(f"<tr>{cells}</tr>")

    table_html = (
        "<table><thead>"
        + header
        + "</thead><tbody>"
        + "".join(body_rows)
        + "</tbody></table>"
    )
    return table_html


CSS = """<style>
body{font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;margin:20px;}
h1{font-size:20px;margin-bottom:4px;}
p.hint{font-size:13px;color:#666;margin-top:0;margin-bottom:16px;}
table{border-collapse:collapse;width:100%;font-size:13px;}
th,td{padding:8px 10px;border-bottom:1px solid #eee;vertical-align:top;}
th{text-align:left;background:#fafafa;}
a{color:#0a58ca;text-decoration:none;}
a:hover{text-decoration:underline;}
.badge{display:inline-block;padding:2px 8px;border-radius:12px;background:#eef;border:1px solid #dde;}
</style>"""


def _wrap_html(inner: str, title: str = "Venue Preview") -> str:
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<title>{title}</title>{CSS}</head><body>"
        "<h1>Venue Preview</h1>"
        "<p class='hint'>This is a quick on-screen preview. "
        "Use <code>/rank/run</code> for JSON/CSV/XLSX exports.</p>"
        + inner
        + "</body></html>"
    )


# -----------------------
# Routes
# -----------------------


@router.post("/run")
def run_rank(payload: RankPayload):
    """JSON-oriented endpoint (for future CSV/XLSX export)."""
    geo_anchors = anchors.compute_anchors(payload)

    google_list = places.discover(payload)
    # Yelp integration is not wired yet; pass an empty list for now
    candidates = merge.merge_candidates(google_list, [])

    filtered = _final_radius_filter(candidates, geo_anchors, payload.radius)
    ranked = _rank_inline(filtered)
    return {"count": len(ranked), "results": ranked}


@router.post("/preview", response_class=HTMLResponse)
def preview(
    request: Request,
    city: str = Query("", description="City name, e.g. 'Clarkston'"),
    zips: str = Query("", description="Comma-separated ZIP codes"),
    miles: float = Query(6.0, description="Radius in miles"),
    topic: str = Query("tir", description="Seminar topic (TIR/EP/SS/etc.)"),
):
    """UI helper – used by /ui page for quick visual previews."""
    payload = RankPayload.from_ui(city, zips, miles, topic)

    geo_anchors = anchors.compute_anchors(payload)
    google_list = places.discover(payload)
    candidates = merge.merge_candidates(google_list, [])

    filtered = _final_radius_filter(candidates, geo_anchors, payload.radius)
    ranked = _rank_inline(filtered)
    html_table = _to_html_table(ranked[:200])  # cap to keep UI snappy

    return HTMLResponse(_wrap_html(html_table))


@router.get("/sample", response_class=HTMLResponse)
def sample(request: Request):
    """Tiny helper for quick manual smoke testing from the browser."""
    sample_payload = RankPayload(
        city="Clarkston",
        zips=["48348"],
        radius=6.0,
        topic="tir",
    )
    geo_anchors = anchors.compute_anchors(sample_payload)
    google_list = places.discover(sample_payload)
    candidates = merge.merge_candidates(google_list, [])

    filtered = _final_radius_filter(candidates, sample_payload.radius, sample_payload.radius)
    ranked = _rank_inline(filtered)
    html_table = _to_html_table(ranked[:100])
    return HTMLResponse(_wrap_html(html_table, title="Sample Venue Preview"))


