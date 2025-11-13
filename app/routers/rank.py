from fastapi import APIRouter
from fastapi.responses import HTMLResponse, JSONResponse

from app.services import extract, merge, places, yelp  # yelp kept for future, but not used

router = APIRouter()

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------


def _extract_state_from_address(addr: str | None) -> str | None:
    """
    Try to pull a 2-letter state code from a formatted address string.

    Examples:
      "123 Main St, Clarkston, MI 48348, USA" -> "MI"
      "Denver, CO 80207, USA"                -> "CO"
    """
    if not addr:
        return None

    parts = [p.strip() for p in addr.split(",") if p.strip()]
    if len(parts) < 2:
        return None

    # Usually the second-to-last part is "MI 48348" or just "MI"
    state_zip = parts[-2]
    tokens = state_zip.split()
    if not tokens:
        return None

    code = tokens[0].strip()
    if len(code) == 2 and code.isalpha():
        return code.upper()

    return None


def _resolve_state(venue: dict) -> str | None:
    """
    Get the most reliable state we can find for a venue.
    Priority:
      1) Parsed from raw.formatted_address
      2) venue["state"] if present
    """
    raw = venue.get("raw") or {}
    addr = raw.get("formatted_address") or raw.get("address")
    parsed = _extract_state_from_address(addr)
    if parsed:
        return parsed

    # Fallback to any existing state field
    state = venue.get("state")
    if isinstance(state, str) and len(state) == 2:
        return state.upper()

    return None


def _filter_by_geography(
    candidates: list[dict],
    payload: dict,
) -> list[dict]:
    """
    Enforce geographic constraints:
      - Must match requested state (if provided)
      - Must be within radius_miles (if both distance_miles and radius_miles present)
    """
    requested_state = (payload.get("state") or "").strip().upper()
    radius = payload.get("radius_miles")

    filtered: list[dict] = []

    for v in candidates:
        # -------- State filter --------
        if requested_state:
            venue_state = _resolve_state(v)
            if not venue_state or venue_state != requested_state:
                # Wrong state → drop it
                continue

        # -------- Radius filter (optional) --------
        if radius is not None:
            try:
                dist = float(v.get("distance_miles", 0))
            except (TypeError, ValueError):
                dist = None

            if dist is not None and dist > float(radius) + 0.25:
                # Add a small buffer just in case, but enforce radius
                continue

        filtered.append(v)

    return filtered


def _rank_inline(enriched_list: list[dict]) -> list[dict]:
    """
    Inline ranking / scoring logic.

    Assumes each venue dict has a 'score' field.
    """
    items = list(enriched_list)  # defensive copy
    items.sort(key=lambda v: v.get("score", 0.0), reverse=True)

    for i, v in enumerate(items, start=1):
        v["rank"] = i

    return items


def _to_html_table(ranked: list[dict]) -> str:
    """
    Render a simple HTML table for the preview UI.
    """
    if not ranked:
        return "<p>No venues found for this query.</p>"

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

    th = "".join(f"<th>{label}</th>" for _, label in columns)

    rows_html = []
    for v in ranked:
        tds = []
        for key, _label in columns:
            val = v.get(key, "")
            if key == "url" and val:
                cell = f'<a href="{val}" target="_blank" rel="noopener noreferrer">{val}</a>'
            else:
                cell = str(val)
            tds.append(f"<td>{cell}</td>")
        rows_html.append("<tr>" + "".join(tds) + "</tr>")

    body = "\n".join(rows_html)

    return f"""
    <table class="results">
      <thead>
        <tr>{th}</tr>
      </thead>
      <tbody>
        {body}
      </tbody>
    </table>
    """


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
    """
    Preview ranked venues for an arbitrary payload from the UI.
    Google-only for now; Yelp is currently disabled.
    """
    # Discover venues from Google Places
    google_list = places.discover(payload)

    # Yelp integration is temporarily disabled; keep empty list for merge API
    yelp_list: list[dict] = []

    # Merge and de-dupe
    candidates = merge.merge_candidates(google_list, yelp_list)

    # Enforce geographic rules (state + radius)
    candidates = _filter_by_geography(candidates, payload)

    # Enrich and rank
    enriched = [extract.enrich(v) for v in candidates]
    ranked = _rank_inline(enriched)

    table_html = _to_html_table(ranked)
    return _wrap_html(table_html, title="Venue Preview")


@router.get("/sample", response_class=HTMLResponse)
def preview_sample():
    """
    Convenience endpoint for debugging: uses a hard-coded payload.
    """
    payload = {
        "cities": ["Clarkston"],
        "zips": [],
        "state": "MI",
        "radius_miles": 6,
        "window_start": "2025-05-01",
        "window_end": "2025-05-15",
        "attendees": 40,
        "preferred_slots": ["11:00", "18:00"],
    }

    google_list = places.discover(payload)
    yelp_list: list[dict] = []
    candidates = merge.merge_candidates(google_list, yelp_list)
    candidates = _filter_by_geography(candidates, payload)

    enriched = [extract.enrich(v) for v in candidates]
    ranked = _rank_inline(enriched)

    table_html = _to_html_table(ranked)
    return _wrap_html(table_html, title="Sample Venue Preview")


@router.post("/json", response_class=JSONResponse)
def rank_json(payload: dict):
    """
    JSON version of the ranking for future API / automation.
    """
    google_list = places.discover(payload)
    yelp_list: list[dict] = []
    candidates = merge.merge_candidates(google_list, yelp_list)
    candidates = _filter_by_geography(candidates, payload)

    enriched = [extract.enrich(v) for v in candidates]
    ranked = _rank_inline(enriched)
    return ranked


    enriched = [extract.enrich(v) for v in candidates]
    ranked = _rank_inline(enriched)
    return ranked

