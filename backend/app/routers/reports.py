from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app import storage
from app.services.pdf_report import generate_case_report

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post("/generate/{change_id}")
async def generate_report(change_id: str):
    change = storage.get("changes", change_id)
    if not change:
        raise HTTPException(404, "Change not found")
    if change.get("priority_score") is None:
        raise HTTPException(400, "Score this case before generating a report")

    report_id = storage.new_id("report_")
    path = generate_case_report(change, report_id)
    storage.put(
        "reports",
        report_id,
        {"id": report_id, "change_id": change_id, "path": path, "created_at": storage.now_iso()},
    )
    return {"report_id": report_id, "change_id": change_id}


@router.get("/download/{report_id}")
async def download_report(report_id: str):
    rec = storage.get("reports", report_id)
    if not rec:
        raise HTTPException(404, "Report not found")
    return FileResponse(rec["path"], media_type="application/pdf", filename=f"{report_id}.pdf")


@router.get("/list")
async def list_reports():
    return storage.list_all("reports")