from fastapi import APIRouter
from app.services import extract

router = APIRouter()

@router.post("/enrich")
def enrich(details_payload: dict):
    venues = details_payload.get("venues", [])
    enriched = []
    for v in venues:
        enriched.append(extract.enrich(v))
    return {"count": len(enriched), "venues": enriched}
