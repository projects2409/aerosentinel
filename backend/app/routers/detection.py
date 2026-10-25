from fastapi import APIRouter, HTTPException

from app import storage
from app.services.yolo_service import is_mock_mode, run_detection

router = APIRouter(prefix="/api/detection", tags=["detection"])


@router.post("/run/{survey_id}")
async def run_detection_for_survey(survey_id: str):
    survey = storage.get("surveys", survey_id)
    if not survey:
        raise HTTPException(404, "Survey not found")

    raw_dets = run_detection(survey["image_path"])
    stored = []
    for d in raw_dets:
        det_id = storage.new_id("det_")
        record = {
            "id": det_id,
            "survey_id": survey_id,
            "class_name": d["class_name"],
            "confidence": d["confidence"],
            "bbox": d["bbox"].model_dump(),
            "mock": d["mock"],
        }
        storage.put("detections", det_id, record)
        stored.append(record)

    storage.update("surveys", survey_id, {"detections_run": True})
    return {
        "survey_id": survey_id,
        "mock_mode": is_mock_mode(),
        "count": len(stored),
        "detections": stored,
    }


@router.get("/survey/{survey_id}")
async def get_detections_for_survey(survey_id: str):
    all_dets = storage.list_all("detections")
    return [d for d in all_dets if d["survey_id"] == survey_id]


@router.get("/mode")
async def detection_mode():
    return {"mock_mode": is_mock_mode()}