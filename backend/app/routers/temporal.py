from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app import storage
from app.services.matching import build_change_records

router = APIRouter(prefix="/api/temporal", tags=["temporal"])


class CompareRequest(BaseModel):
    survey_ids: list[str]  # chronological order, e.g. [T1_id, T2_id, T3_id]


@router.post("/compare")
async def compare_surveys(req: CompareRequest):
    if len(req.survey_ids) < 2:
        raise HTTPException(400, "Need at least 2 surveys to compare")

    surveys = []
    for sid in req.survey_ids:
        s = storage.get("surveys", sid)
        if not s:
            raise HTTPException(404, f"Survey {sid} not found")
        surveys.append(s)

    all_dets = storage.list_all("detections")
    detections_by_survey = {}
    for sid in req.survey_ids:
        detections_by_survey[sid] = [d for d in all_dets if d["survey_id"] == sid]
        if not detections_by_survey[sid]:
            raise HTTPException(
                400, f"Survey {sid} has no detections yet — run detection first"
            )

    changes = build_change_records(surveys, detections_by_survey)

    stored = []
    for c in changes:
        change_id = storage.new_id("change_")
        record = {"id": change_id, **c}
        storage.put("changes", change_id, record)
        stored.append(record)

    return {"survey_ids": req.survey_ids, "change_count": len(stored), "changes": stored}


@router.get("/changes")
async def list_changes():
    return storage.list_all("changes")


@router.get("/changes/{change_id}")
async def get_change(change_id: str):
    c = storage.get("changes", change_id)
    if not c:
        raise HTTPException(404, "Change not found")
    return c