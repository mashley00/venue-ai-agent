from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()


HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Venue Search</title>
  <style>
    body {
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      margin: 0;
      padding: 0;
      background: #f5f5f7;
      color: #111827;
    }
    .container {
      max-width: 1100px;
      margin: 2rem auto 3rem;
      padding: 1.5rem 2rem 2rem;
      background: #ffffff;
      border-radius: 0.75rem;
      box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
    }
    h1 {
      margin-top: 0;
      font-size: 1.75rem;
      margin-bottom: 1.25rem;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
      gap: 1rem 1.5rem;
    }
    label {
      display: block;
      font-weight: 600;
      font-size: 0.9rem;
      margin-bottom: 0.25rem;
    }
    input[type="text"],
    input[type="number"],
    input[type="date"] {
      width: 100%;
      padding: 0.5rem 0.6rem;
      border-radius: 0.4rem;
      border: 1px solid #d1d5db;
      font-size: 0.9rem;
      box-sizing: border-box;
    }
    input[type="number"] {
      -moz-appearance: textfield;
    }
    input[type="number"]::-webkit-outer-spin-button,
    input[type="number"]::-webkit-inner-spin-button {
      -webkit-appearance: none;
      margin: 0;
    }
    .hint {
      font-size: 0.75rem;
      color: #6b7280;
      margin-top: 0.15rem;
    }
    .actions {
      margin-top: 1.25rem;
      display: flex;
      align-items: center;
      gap: 1rem;
    }
    button {
      background: #2563eb;
      color: #ffffff;
      border: none;
      border-radius: 9999px;
      padding: 0.6rem 1.4rem;
      font-size: 0.9rem;
      font-weight: 600;
      cursor: pointer;
    }
    button:hover {
      background: #1d4ed8;
    }
    .status {
      font-size: 0.9rem;
      color: #6b7280;
    }
    .table-container {
      margin-top: 2rem;
      overflow-x: auto;
      border-radius: 0.75rem;
      border: 1px solid #e5e7eb;
      background: #ffffff;
      max-height: 520px;
    }
    table {
      border-collapse: collapse;
      width: 100%;
      min-width: 800px;
      font-size: 0.85rem;
    }
    thead {
      position: sticky;
      top: 0;
      background: #f3f4f6;
      z-index: 1;
    }
    th,
    td {
      padding: 0.55rem 0.7rem;
      border-bottom: 1px solid #e5e7eb;
      text-align: left;
      vertical-align: top;
    }
    th {
      font-weight: 600;
      color: #374151;
      white-space: nowrap;
      cursor: pointer;
      user-select: none;
    }
    th.sort-asc::after {
      content: " ▲";
      font-size: 0.7rem;
    }
    th.sort-desc::after {
      content: " ▼";
      font-size: 0.7rem;
    }
    tbody tr:nth-child(even) {
      background: #f9fafb;
    }
    .pill {
      display: inline-flex;
      align-items: center;
      padding: 0.15rem 0.45rem;
      border-radius: 999px;
      background: #eff6ff;
      color: #1d4ed8;
      font-size: 0.7rem;
      font-weight: 600;
    }
    .badge-source {
      background: #ecfeff;
      color: #0891b2;
    }
    .badge-existing {
      background: #ecfdf5;
      color: #16a34a;
    }
    .no-results {
      margin-top: 1.5rem;
      font-size: 0.9rem;
      color: #6b7280;
    }
    .json-debug {
      margin-top: 1.5rem;
      font-size: 0.75rem;
      color: #9ca3af;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono","Courier New", monospace;
      white-space: pre-wrap;
      word-break: break-all;
      display: none;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>Venue Search</h1>

    <form id="search-form">
      <div class="grid">
        <div>
          <label for="cities">Cities (comma-separated)</label>
          <input id="cities" type="text" placeholder="Greenville, NC; Kinston" />
          <div class="hint">Up to 3 cities (e.g., Greenville, NC; Kinston, NC)</div>
        </div>

        <div>
          <label for="zips">ZIP Codes (comma-separated)</label>
          <input id="zips" type="text" placeholder="48348, 48346" />
          <div class="hint">Up to 6 ZIPs</div>
        </div>

        <div>
          <label for="start_date">Start Date</label>
          <input id="start_date" type="date" />
        </div>

        <div>
          <label for="end_date">End Date</label>
          <input id="end_date" type="date" />
        </div>

        <div>
          <label for="radius_miles">Radius (miles)</label>
          <input id="radius_miles" type="number" value="6" min="1" max="50" />
          <div class="hint">Default is 6 miles</div>
        </div>

        <div>
          <label for="attendees">Attendees</label>
          <input id="attendees" type="number" value="30" min="1" />
          <div class="hint">Default 30</div>
        </div>
      </div>

      <div class="actions">
        <button type="submit">Search</button>
        <div id="status" class="status"></div>
      </div>
    </form>

    <div id="results-container" class="table-container" style="display:none;">
      <table id="results-table">
        <thead>
          <tr>
            <th data-sort-key="index">#</th>
            <th data-sort-key="name">Venue</th>
            <th data-sort-key="room_name">Room</th>
            <th data-sort-key="category">Category</th>
            <th data-sort-key="city">City</th>
            <th data-sort-key="state">State</th>
            <th data-sort-key="distance_miles">Miles</th>
            <th data-sort-key="score">Score</th>
            <th data-sort-key="source">Source</th>
            <th data-sort-key="educationality">Edu</th>
            <th data-sort-key="availability_score">Avail</th>
            <th data-sort-key="capacity_score">Cap</th>
            <th data-sort-key="amenities_score">Ams</th>
            <th data-sort-key="logistics_score">Log</th>
          </tr>
        </thead>
        <tbody id="results-body"></tbody>
      </table>
    </div>

    <div id="no-results" class="no-results" style="display:none;">
      No venues found for the current search. Try adjusting radius, cities, or ZIP codes.
    </div>

    <pre id="json-debug" class="json-debug"></pre>
  </div>

  <script>
    const form = document.getElementById("search-form");
    const statusEl = document.getElementById("status");
    const resultsContainer = document.getElementById("results-container");
    const resultsBody = document.getElementById("results-body");
    const noResultsEl = document.getElementById("no-results");
    const jsonDebug = document.getElementById("json-debug");
    const table = document.getElementById("results-table");
    let currentRows = [];
    let currentSortKey = "score";
    let currentSortDir = "desc";

    function parseList(value, maxCount) {
      if (!value) return [];
      const parts = value
        .replace(/;/g, ",")
        .split(",")
        .map((v) => v.trim())
        .filter(Boolean);
      if (maxCount && parts.length > maxCount) {
        return parts.slice(0, maxCount);
      }
      return parts;
    }

    function buildPayload() {
      const citiesInput = document.getElementById("cities").value;
      const zipsInput = document.getElementById("zips").value;
      const startDate = document.getElementById("start_date").value;
      const endDate = document.getElementById("end_date").value;
      const radiusMiles = document.getElementById("radius_miles").value;
      const attendees = document.getElementById("attendees").value;

      const cities = parseList(citiesInput, 3);
      const zips = parseList(zipsInput, 6);

      const payload = {
        cities,
        zips,
        radius_miles: radiusMiles ? Number(radiusMiles) : 6,
        attendees: attendees ? Number(attendees) : 30,
      };

      if (startDate) payload["start_date"] = startDate;
      if (endDate) payload["end_date"] = endDate;

      // For downstream text-based geography filters, set city/state from first city if present
      if (cities.length > 0) {
        // Expect "City, ST" or "City ST"
        const first = cities[0];
        const parts = first.split(",");
        if (parts.length >= 2) {
          payload["city"] = parts[0].trim();
          payload["state"] = parts[1].trim();
        } else {
          payload["city"] = first.trim();
        }
      }
      if (zips.length > 0) {
        payload["zip_codes"] = zips;
      }

      return payload;
    }

    function clearSortIndicators() {
      const ths = table.querySelectorAll("th[data-sort-key]");
      ths.forEach((th) => {
        th.classList.remove("sort-asc");
        th.classList.remove("sort-desc");
      });
    }

    function applySortIndicator() {
      clearSortIndicators();
      const th = table.querySelector(`th[data-sort-key="${currentSortKey}"]`);
      if (!th) return;
      th.classList.add(currentSortDir === "asc" ? "sort-asc" : "sort-desc");
    }

    function renderRows() {
      resultsBody.innerHTML = "";
      if (!currentRows.length) {
        resultsContainer.style.display = "none";
        noResultsEl.style.display = "block";
        return;
      }

      noResultsEl.style.display = "none";
      resultsContainer.style.display = "block";

      const sorted = [...currentRows].sort((a, b) => {
        const key = currentSortKey;
        const av = a[key];
        const bv = b[key];

        if (av == null && bv == null) return 0;
        if (av == null) return 1;
        if (bv == null) return -1;

        // numeric sort when both look like numbers
        const aNum = Number(av);
        const bNum = Number(bv);
        const bothNumeric = !Number.isNaN(aNum) && !Number.isNaN(bNum);

        let cmp;
        if (bothNumeric) {
          cmp = aNum - bNum;
        } else {
          cmp = String(av).localeCompare(String(bv));
        }

        return currentSortDir === "asc" ? cmp : -cmp;
      });

      sorted.forEach((row, idx) => {
        const tr = document.createElement("tr");

        const fields = {
          index: idx + 1,
          name: row.name || "",
          room_name: row.room_name || "",
          category: row.category || "",
          city: row.city || "",
          state: row.state || "",
          distance_miles: row.distance_miles != null ? row.distance_miles : "",
          score: row.score != null ? row.score.toFixed ? row.score.toFixed(2) : row.score : "",
          source: row.source || "",
          educationality: row.educationality != null ? row.educationality : "",
          availability_score: row.availability_score != null ? row.availability_score : "",
          capacity_score: row.capacity_score != null ? row.capacity_score : "",
          amenities_score: row.amenities_score != null ? row.amenities_score : "",
          logistics_score: row.logistics_score != null ? row.logistics_score : "",
        };

        function td(text) {
          const cell = document.createElement("td");
          cell.textContent = text;
          return cell;
        }

        tr.appendChild(td(fields.index));
        tr.appendChild(td(fields.name));
        tr.appendChild(td(fields.room_name));
        tr.appendChild(td(fields.category));
        tr.appendChild(td(fields.city));
        tr.appendChild(td(fields.state));
        tr.appendChild(td(fields.distance_miles));
        tr.appendChild(td(fields.score));

        const sourceTd = document.createElement("td");
        if (fields.source) {
          const span = document.createElement("span");
          span.className = "pill badge-source";
          span.textContent = fields.source;
          sourceTd.appendChild(span);
        }
        tr.appendChild(sourceTd);

        tr.appendChild(td(fields.educationality));
        tr.appendChild(td(fields.availability_score));
        tr.appendChild(td(fields.capacity_score));
        tr.appendChild(td(fields.amenities_score));
        tr.appendChild(td(fields.logistics_score));

        resultsBody.appendChild(tr);
      });

      applySortIndicator();
    }

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      statusEl.textContent = "Searching venues…";
      resultsContainer.style.display = "none";
      noResultsEl.style.display = "none";
      jsonDebug.style.display = "none";

      const payload = buildPayload();

      try {
        const res = await fetch("/rank/preview", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });

        if (!res.ok) {
          statusEl.textContent = "Error: " + res.status + " " + res.statusText;
          return;
        }

        const data = await res.json();
        // Expect { results: [...], candidates: [...] }
        const results = Array.isArray(data.results) ? data.results : [];

        currentRows = results;
        statusEl.textContent = `${results.length} venue(s) found.`;
        jsonDebug.textContent = JSON.stringify(data, null, 2);  // keep as hidden debug
        renderRows();
      } catch (err) {
        console.error(err);
        statusEl.textContent = "Error performing search.";
      }
    });

    // Sorting behaviour
    table.querySelectorAll("th[data-sort-key]").forEach((th) => {
      th.addEventListener("click", () => {
        const key = th.getAttribute("data-sort-key");
        if (!key) return;
        if (currentSortKey === key) {
          currentSortDir = currentSortDir === "asc" ? "desc" : "asc";
        } else {
          currentSortKey = key;
          currentSortDir = key === "index" ? "asc" : "desc";
        }
        renderRows();
      });
    });

    // Initial sort indicator
    applySortIndicator();
  </script>
</body>
</html>
"""


@router.get("/ui", response_class=HTMLResponse)
def ui() -> HTMLResponse:
    """
    Simple HTML UI for venue search that posts to /rank/preview
    and renders a sortable table of results.
    """
    return HTMLResponse(content=HTML_PAGE)



