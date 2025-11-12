from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from typing import List
import pandas as pd

from app.services import scoring, places, yelp, extract, merge

router = APIRouter()

# -----------------------
# Shared helpers
# -----------------------

TABLE_COLUMNS = [
    ("rank", "Rank"),
    ("name", "Venue"),
    ("category", "Category"),
    ("educationality", "Edu"),
    ("city", "City"),
    ("distance_miles", "Mi"),
    ("availability_status", "Avail"),
    ("website_url", "Website"),
    ("booking_url", "Booking"),
    ("phone", "Phone"),
    ("reason_text", "Why this rank"),
]

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

def _to_html_table(ranked: List[dict]) -> str:
    rows = []
    for v in ranked:
        row = {col_key: v.get(col_key) for col_key, _ in TABLE_COLUMNS}
        rows.append(row)
    if not rows:
        df = pd.DataFrame(columns=[h for _, h in TABLE_COLUMNS])
    else:
        df = pd.DataFrame(rows)
        df.columns = [h for _, h in TABLE_COLUMNS]
    return df.to_html(index=False, border=0, escape=False)

CSS = """
<style>
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;margin:24px;}
h1{margin:0 0 12px 0;font-size:22px}
p.hint{margin:4px 0 16px 0;color:#666}
table{border-collapse:collapse;width:100%}
th,td{padding:10px;border-bottom:1px solid #eee;vertical-align:top}
th{text-align:left;background:#fafafa}
a{color:#0a58ca;text-decoration:none}
a:hover{text-decoration:underline}
.badge{display:inline-block;padding:2px 8px;border-radius:12px;background:#eef;border:1px solid #dde}
</style>
"""

def _wrap_html(inner: str, title="Venue Preview") -> str:
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<title>{title}</title>{CSS}</head><body>"
        "<h1>Venue Preview</h1>"
        "<p class='hint'>This is a quick on-screen preview. "
        "Use <code>/rank/run</code> for JSON/CSV/XLSX exports.</p>"
        f"{inner}</body></html>"
    )

# -----------------------
# API: JSON rank (kept for automation/export)
# -----------------------

@router.post("/run")
def run_rank(payload: dict):
    # 1) Discover (Google + Yelp) and merge/de-dupe
    candidates = merge.merge_candidates(
        places.discover(payload),
        yelp.discover(payload)
    )
    # 2) Enrich (stub for now)
    enriched = [extract.enrich(v) for v in candidates]
    # 3) Rank
    ranked = _rank_inline(enriched)

    # Optional export for automation consumers
    df = pd.DataFrame(ranked)
    csv_path = "exports/venues_ranked.csv"
    xlsx_path = "exports/venues_ranked.xlsx"
    try:
        df.to_csv(csv_path, index=False)
    except Exception as _:
        pass
    try:
        df.to_excel(xlsx_path, index=False)
    except Exception as _:
        pass

    return {"results": ranked, "export_csv": csv_path, "export_xlsx": xlsx_path}

# -----------------------
# API: HTML preview endpoints
# -----------------------

@router.post("/preview", response_class=HTMLResponse)
def preview(payload: dict):
    # 1) Discover (Google + Yelp) and merge/de-dupe
    candidates = merge.merge_candidates(
        places.discover(payload),
        yelp.discover(payload)
    )
    # 2) Enrich (stub for now)
    enriched = [extract.enrich(v) for v in candidates]
    # 3) Rank and render
    ranked = _rank_inline(enriched)
    table_html = _to_html_table(ranked)
    return _wrap_html(table_html, title="Venue Preview")

@router.get("/preview-sample", response_class=HTMLResponse)
def preview_sample():
    payload = {
        "cities": ["Greenville, NC"],
        "zips": ["27834"],
        "radius_miles": 6,
        "window_start": "2025-05-08",
        "window_end": "2025-05-22",
        "attendees": 30,
        "preferred_slots": ["11:00","11:30","18:00","18:30"]
    }
    candidates = merge.merge_candidates(
        places.discover(payload),
        yelp.discover(payload)
    )
    enriched = [extract.enrich(v) for v in candidates]
    ranked = _rank_inline(enriched)
    table_html = _to_html_table(ranked)
    return _wrap_html(table_html, title="Venue Preview (Sample)")

