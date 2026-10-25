from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import FRONTEND_ORIGINS, UPLOADS_DIR
from app.routers import (
    detection,
    drone,
    geospatial,
    priority,
    reports,
    temporal,
    upload,
)


app = FastAPI(
    title="AeroSentinel Prototype API",
    description=(
        "AeroSentinel prototype for temporal aerial change detection, "
        "CDAC YOLO drone monitoring, priority ranking and automatic "
        "evidence reporting."
    ),
    version="0.2.0-prototype",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Existing APIs
app.include_router(upload.router)
app.include_router(detection.router)
app.include_router(temporal.router)
app.include_router(geospatial.router)
app.include_router(priority.router)
app.include_router(reports.router)

# New drone API
app.include_router(drone.router)


# Uploaded images/evidence/PDF-related media
app.mount(
    "/media",
    StaticFiles(directory=UPLOADS_DIR),
    name="media",
)


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "mode": "prototype",
    }