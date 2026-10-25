from fastapi import APIRouter, HTTPException
from PIL import Image

from app import storage
from app.services.geospatial import analyze_point, load_boundaries, pixel_to_lonlat

router = APIRouter(prefix="/api/geospatial", tags=["geospatial"])


@router.get("/boundaries")
async def get_boundaries():
    gdf = load_boundaries()
    return gdf.to_json()


@router.post("/analyze/{change_id}")
async def analyze_change(change_id: str):
    change = storage.get("changes", change_id)
    if not change:
        raise HTTPException(404, "Change not found")

    # Use the first survey in the chain as the georeferencing anchor.
    survey = storage.get("surveys", change["survey_ids"][0])
    if not survey or survey.get("lat") is None or survey.get("lon") is None:
        raise HTTPException(
            400,
            "Reference survey has no lat/lon set — provide coordinates at upload time "
            "to enable geospatial analysis for this prototype.",
        )

    with Image.open(survey["image_path"]) as img:
        w, h = img.size

    px, py = change["centroid_px"]
    lon, lat = pixel_to_lonlat(survey["lat"], survey["lon"], w, h, px, py)
    geo = analyze_point(lon, lat)
    geo["lon"] = lon
    geo["lat"] = lat

    storage.update(
        "changes",
        change_id,
        {
            "inside_boundary": geo["inside_boundary"],
            "distance_to_boundary_px": geo["distance_to_boundary_px"],
            "zone_name": geo["zone_name"],
            "lon": lon,
            "lat": lat,
        },
    )
    return geo