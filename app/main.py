from fastapi import FastAPI
from app.routers import discover, details, rank

app = FastAPI(title="Venue Agent", version="0.1.0")

app.include_router(discover.router, prefix="/discover", tags=["discover"])
app.include_router(details.router,  prefix="/details",  tags=["details"])
app.include_router(rank.router,     prefix="/rank",     tags=["rank"])

@app.get("/health")
def health():
    return {"ok": True}
