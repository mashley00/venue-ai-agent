from fastapi import APIRouter
from fastapi.responses import HTMLResponse, JSONResponse

from app.services import extract, merge, places, yelp

router = APIRouter()

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------


def _rank_inline(enriched_list: list[dict]) -> list[dict]:
    """
    Inline ranking / scoring logic.

    Assumes each venue dict has:
      - score (float)
    and other metadata fields.
    """
    # Defensive copy
    items = list(enriched_list)

    # Sort descending by score
    items.sort(key=lambda v: v.get("score", 0.0), reverse=True)

    # Add rank field
    for i, v in enumerate(items, start=1):
        v["rank"] = i

    return items


def _to_html_table(ranked: list[dict]) -> str:
    """
    Render a simple HTML table for the preview UI.
    """
    if not ranked:
        return "<p>No venues found for this query.</p>"

    # Define visible columns and headers
    columns = [
        ("rank", "Rank"),
        ("name", "Venue Name"),
        ("venue_type", "Type"),
        ("city", "City"),
        ("distance_miles", "Miles"),
        ("source", "Source"),
        ("url", "URL"),
        ("phone", "Phone"),
        ("education_score", "Edu"),
        ("availability_score", "Avail"),
        ("capacity_score", "Cap"),
        ("ams_score", "Ams"),
        ("log_score", "Log"),
    ]

    # Build header
    th = "".join(f"<th>{label}</th>" for _, label in columns)

    rows_html = []
    for v in ranked:
        tds = []
        for key, _ in columns:
            val = v.get(key, "")
            if key == "url" and val:
                cell = f'<a href="{val}" target="_blank" rel="noopener noreferrer">{val}</a>'
            else:
                cell = str(val)
            tds.append(f"<td>{cell}</td>")
        rows_html.append("<tr>" + "".join(tds) + "</tr>")

    body = "\n".join(rows_html)

    table = f"""
    <table class="results">
      <thead>
        <tr>{th}</tr>
      </thead>
      <tbody>
        {body}
      </tbody>
    </table>
    """
    return table


def _wrap_html(content: str, title: str = "Venue Preview") -> str:
    """
    Basic HTML wrapper used by the /rank/preview endpoint.
    """
    return f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>{title}</title>
  <style>
    body {{
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      margin: 1.5rem;
      background: #f6f7fb;
      color: #111827;
    }}
    h1 {{
      font-size: 1.5rem;
      margin-bottom: 1rem;
    }}
    table.results {{
      border-collapse: collapse;
      width: 100%;
      background: white;
      box-shadow: 0 1px 3px rgba(15, 23, 42, 0.12);
      border-radius: 0.5rem;
      overflow: hidden;
    }}
    table.results th,
    table.results td {{
      padding: 0.5rem 0.75rem;
      border-bottom: 1px solid #e5e7eb;
      font-size: 0.85rem;
      vertical-align: top;
    }}
    table.results th {{
      background: #f3f4f6;
      text-align: left;
      font-weight: 600;
      white-space: nowrap;
    }}
    table.results tr:nth-child(even) td {{
      background: #f9fafb;
    }}
    a {{
      color: #2563eb;
      text-decoration: none;
    }}
    a:hover {{
      text-decoration: underline;
    }}
    .notice {{
      margin-bottom: 1rem;
      padding: 0.75rem 1rem;
      border-radius: 0.5rem;
      background: #eff6ff;
      color: #1d4ed8;
      font-size: 0.85rem;
    }}
  </style>
</head>
<body>
  <h1>{title}</h1>
  {content}
</body>
</html>
    """.strip()


# -----------------------------------------------------------------------------
# API endpoints
# -----------------------------------------------------------------------------


@router.post("/preview", response_class=HTMLResponse)
def preview(payload: dict):
    """Preview ranked venues for an arbitrary payload from the UI."""
    # Discover venues from Google Places
    google_list = places.discover(payload)

    # NOTE: Yelp integration temporarily disabled; keep empty list to satisfy merge API
    yelp_list: list[dict] = []

    # Merge and de-dupe candidate lists
    candidates = merge.merge_candidates(google_list, yelp_list)

    # Enrich and rank
    enriched = [extract.enrich(v) for v in candidates]
    ranked = _rank_inline(enriched)

    table_html = _to_html_table(ranked)
    return _wrap_html(table_html, title="Venue Preview")


@router.get("/sample", response_class=HTMLResponse)
def preview_sample():
    """
    Convenience endpoint for debugging:
    uses a hard-coded payload instead of the UI form.
    """
    payload = {
        "cities": ["Clarkston"],
        "zips": [],
        "radius_miles": 6,
        "window_start": "2025-05-01",
        "window_end": "2025-05-15",
        "attendees": 40,
        "preferred_slots": ["11:00", "18:00"],
    }

    google_list = places.discover(payload)
    yelp_list: list[dict] = []
    candidates = merge.merge_candidates(google_list, yelp_list)

    enriched = [extract.enrich(v) for v in candidates]
    ranked = _rank_inline(enriched)

    table_html = _to_html_table(ranked)
    return _wrap_html(table_html, title="Sample Venue Preview")


@router.post("/json", response_class=JSONResponse)
def rank_json(payload: dict):
    """
    JSON version of the ranking, useful for future API / automation.
    """
    google_list = places.discover(payload)
    yelp_list: list[dict] = []
    candidates = merge.merge_candidates(google_list, yelp_list)

    enriched = [extract.enrich(v) for v in candidates]
    ranked = _rank_inline(enriched)
    return ranked

