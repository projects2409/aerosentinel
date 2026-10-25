from fastapi import APIRouter, HTTPException

from app import storage
from app.services.priority_engine import score_change

router = APIRouter(prefix="/api/priority", tags=["priority"])


@router.post("/score/{change_id}")
async def score_case(change_id: str):
    change = storage.get("changes", change_id)
    if not change:
        raise HTTPException(404, "Change not found")

    geo = {
        "inside_boundary": change.get("inside_boundary", False),
        "distance_to_boundary_px": change.get("distance_to_boundary_px", 0.0),
        "zone_name": change.get("zone_name", "unassigned"),
    }
    score, reasons, weights = score_change(change, geo)

    updated = storage.update(
        "changes",
        change_id,
        {
            "priority_score": score,
            "priority_reasons": reasons,
            "weights_snapshot": weights,
        },
    )
    return updated


@router.get("/ranked")
async def ranked_cases():
    changes = storage.list_all("changes")
    scored = [c for c in changes if c.get("priority_score") is not None]
    return sorted(scored, key=lambda c: c["priority_score"], reverse=True)