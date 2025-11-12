# Venue Agent (Option A — FastAPI + API-first)

This is a production-ready **starter scaffold** for your venue-search agent:
- **FastAPI** service with `/discover`, `/details`, `/rank`
- Pluggable discovery (Google Places + Yelp) with graceful fallback to mocks
- Transparent scoring
- SQLite for local dev (swap to Postgres later)
- Dockerized, with one-line local run

> Use this as your MVP, then hook UiPath or Power Automate to the API and exports.

---

## Quickstart (local, no Docker)

1) **Python 3.11+** recommended.  
2) Create a virtual env and install:
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

3) Copy `.env.example` to `.env` and set keys (optional). Without keys, discovery returns realistic **mock data** so you can test end‑to‑end.

4) Run the API:
```bash
uvicorn app.main:app --reload
```
Open docs: `http://127.0.0.1:8000/docs`

### Example request
`POST /discover/run`
```json
{
  "cities": ["Greenville, NC"],
  "zips": ["27834"],
  "radius_miles": 6,
  "window_start": "2025-05-08",
  "window_end": "2025-05-22",
  "attendees": 30,
  "preferred_slots": ["11:00","11:30","18:00","18:30"]
}
```

Then call:
- `POST /details/enrich` (enriches fields; mocked now)
- `POST /rank/run` (returns stack-ranked list and writes CSV to `exports/`)

---

## Quickstart (Docker)

```bash
docker compose up --build
```
API will be on `http://localhost:8000`

---

## Environment

Create `.env` (see `.env.example`):
```
GOOGLE_MAPS_API_KEY=
YELP_API_KEY=
DATABASE_URL=sqlite:///./local.db
SMTP_HOST=
SMTP_PORT=
SMTP_USER=
SMTP_PASS=
```

> If API keys are empty, the app uses **mock discovery** data so you can test scoring and exports immediately.

---

## Outputs

On `POST /rank/run`, the agent writes:
- `exports/venues_ranked.csv`
- `exports/venues_ranked.xlsx`

Both include a `reason_text` field explaining the score.

---

## Next steps

- Implement Playwright extraction in `app/services/extract.py` (kept as a stub to avoid heavy dependency here).
- Swap SQLite to Postgres by setting `DATABASE_URL`.
- Add email sending in `app/services/emailer.py` (stub provided).
- Wire UiPath/Power Automate to call the API and ingest the CSV/XLSX.

