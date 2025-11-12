from fastapi import FastAPI
from app.routers import discover, details, rank
from app.routers import ui  # <-- add this import

app = FastAPI(title="Venue Agent", version="0.1.0")

@app.get("/")
def root():
    return {"ok": True, "docs": "/docs", "health": "/health", "ui": "/ui"}

# existing routers
app.include_router(discover.router, prefix="/discover", tags=["discover"])
app.include_router(details.router,  prefix="/details",  tags=["details"])
app.include_router(rank.router,     prefix="/rank",     tags=["rank"])

# NEW: register the UI router (no prefix, path = /ui)
app.include_router(ui.router, tags=["ui"])

@app.get("/health")
def health():
    return {"ok": True}
