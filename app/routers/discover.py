from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.deps import get_db, Base, engine
from app.services import places, yelp

router = APIRouter()

# Ensure tables exist (lightweight for MVP)
Base.metadata.create_all(bind=engine)

@router.post("/run")
def run_discover(payload: dict, db: Session = Depends(get_db)):
    # Call providers (Google Places + Yelp); combine & normalize
    candidates = []
    candidates += places.discover(payload)
    candidates += yelp.discover(payload)
    # Deduplicate by name+address
    seen = set()
    unique = []
    for c in candidates:
        key = (c.get("name","").lower(), c.get("address","").lower())
        if key in seen:
            continue
        seen.add(key)
        unique.append(c)
    return {"count": len(unique), "candidates": unique}
