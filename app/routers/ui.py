from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from app.services import places, yelp, extract, scoring

router = APIRouter()

HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Venue Search</title>
  <style>
  body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;margin:24px;max-width:1200px}
  h1{margin:0 0 16px 0;font-size:24px}
  form{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px}
  label{font-weight:600;font-size:14px}
  input,button{padding:10px;font-size:14px}
  input[type="text"],input[type="date"],input[type="number"]{border:1px solid #ccc;border-radius:8px}
  button{border:0;border-radius:8px;background:#0a58ca;color:#fff;cursor:pointer}
  button:hover{opacity:.95}
  .small{color:#666;font-size:12px}
  #result{margin-top:16px}
  table{border-collapse:collapse;width:100%}
  th,td{padding:10px;border-bottom:1px solid #eee;vertical-align:top}
  th{text-align:left;background:#fafafa}
  a{color:#0a58ca;text-decoration:none}
  a:hover{text-decoration:underline}
  .notice{background:#fff8e5;border:1px solid #ffe7a7;padding:10px;border-radius:8px;margin:8px 0;color:#7a5b00}
  </style>
</head>
<body>
<h1>Venue Search</h1>
<div class="notice">Enter either <b>Cities</b> (up to 3) or <b>ZIP Codes</b> (up to 6). Leave the other field blank.</div>

<form id="searchForm">
  <div>
    <label for="cities">Cities (comma-separated)</label>
    <input id="cities" name="cities" type="text" placeholder="Greenville, NC; Kinston, NC" />
    <div class="small">Up to 3 cities (e.g., Greenville, NC; Kinston, NC)</div>
  </div>
  <div>
    <label for="zips">ZIP Codes (comma-separated)</label>
    <input id="zips" name="zips" type="text" placeholder="27834, 27534, 27858" />
    <div class="small">Up to 6 ZIPs</div>
  </div>
  <div>
    <label for="start">Start Date</label>
    <input id="start" name="start" type="date" required />
  </div>
  <div>
    <label for="end">End Date</label>
    <input id="end" name="end" type="date" required />
  </div>
  <div>
    <label for="radius">Radius (miles)</label>
    <input id="radius" name="radius" type="number" min="1" max="15" value="6" />
    <div class="small">Default 6 miles</div>
  </div>
  <div>
    <label for="attendees">Attendees</label>
    <input id="attendees" name="attendees" type="number" min="10" max="60" value="30" />
    <div class="small">Default 30</div>
  </div>
  <div style="grid-column:1 / -1">
    <button type="submit">Search</button>
  </div>
</form>

<div id="result" class="small">Results will appear here.</div>

<script>
const cols = [
  ["rank","Rank"],["name","Venue"],["category","Category"],["educationality","Edu"],
  ["city","City"],["distance_miles","Mi"],["availability_status","Avail"],
  ["website_url","Website"],["booking_url","Booking"],["phone","Phone"],["reason_text","Why this rank"]
];

function toTable(ranked){
  const th = cols.map(c=>"<th>"+c[1]+"</th>").join("");
  const rows = ranked.map(v=>{
    const tds = cols.map(([k,_])=>{
      let val = v[k] ?? "";
      if(k==="website_url" && val) return '<td><a href="'+val+'" target="_blank">website</a></td>';
      if(k==="booking_url" && val) return '<td><a href="'+val+'" target="_blank">booking</a></td>';
      return "<td>"+(val ?? "")+"</td>";
    }).join("");
    return "<tr>"+tds+"</tr>";
  }).join("");
  return "<table><thead><tr>"+th+"</tr></thead><tbody>"+rows+"</tbody></table>";
}

document.getElementById("searchForm").addEventListener("submit", async (e)=>{
  e.preventDefault();
  const citiesRaw = document.getElementById("cities").value.trim();
  const zipsRaw = document.getElementById("zips").value.trim();
  const start = document.getElementById("start").value;
  const end = document.getElementById("end").value;
  const radius = parseFloat(document.getElementById("radius").value || "6");
  const attendees = parseInt(document.getElementById("attendees").value || "30", 10);

  const split = s => s.split(/[,;]+/).map(x=>x.trim()).filter(Boolean);

  const cities = citiesRaw ? split(citiesRaw).slice(0,3) : [];
  const zips = zipsRaw ? split(zipsRaw).slice(0,6) : [];

  if(cities.length===0 && zips.length===0){ alert("Enter cities OR zip codes."); return; }
  if(cities.length>0 && zips.length>0){ alert("Use either cities OR zips, not both."); return; }

  const payload = {
    cities, zips, radius_miles: radius,
    window_start: start, window_end: end,
    attendees, preferred_slots: ["11:00","11:30","18:00","18:30"]
  };

  const res = await fetch("/rank/preview", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify(payload)
  });
  if(!res.ok){
    const text = await res.text();
    document.getElementById("result").innerHTML = '<div class="notice">Error: '+text+'</div>';
    return;
  }
  const html = await res.text();
  document.getElementById("result").innerHTML = html;
});
</script>
</body>
</html>
"""

@router.get("/ui", response_class=HTMLResponse)
def ui():
    return HTML


