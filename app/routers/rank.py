from fastapi import APIRouter
from typing import List
import pandas as pd
from app.services import scoring

router = APIRouter()

@router.post("/run")
def run_rank(payload: dict):
    venues: List[dict] = payload.get("venues", [])
    ranked = []
    for v in venues:
        total, reason, comps = scoring.score(v)
        v["score_total"] = total
        v["reason_text"] = reason
        v["score_components"] = comps
        ranked.append(v)
    ranked.sort(key=lambda x: x.get("score_total", 0), reverse=True)

    # Export to CSV/XLSX
    df = pd.DataFrame(ranked)
    csv_path = "exports/venues_ranked.csv"
    xlsx_path = "exports/venues_ranked.xlsx"
    df.to_csv(csv_path, index=False)
    df.to_excel(xlsx_path, index=False)

    return {"results": ranked, "export_csv": csv_path, "export_xlsx": xlsx_path}
