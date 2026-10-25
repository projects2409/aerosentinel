"""
Geospatial boundary analysis.

IMPORTANT: This prototype uses SAMPLE GeoJSON boundaries
(sample_data/boundaries.geojson), not live government cadastral data.
Never present these polygons as authoritative parcel/land-record data in
the UI or reports — they exist to demonstrate the point-in-polygon /
distance-to-boundary pipeline.

Pixel<->geo mapping here is a simple prototype affine transform (survey
lat/lon treated as the image center, with a configurable pixels-per-degree
scale) — good enough to demonstrate the GeoPandas pipeline end to end, not
a substitute for real georeferencing (e.g. from drone telemetry/EXIF GPS
or ground control points).
"""

import geopandas as gpd
from shapely.geometry import Point

from app.config import BOUNDARIES_PATH

_boundaries_gdf = None

# Prototype-only affine constants for pixel -> lat/lon conversion.
_PX_PER_DEGREE = 100000.0  # arbitrary demo scale


def load_boundaries() -> gpd.GeoDataFrame:
    global _boundaries_gdf
    if _boundaries_gdf is None:
        _boundaries_gdf = gpd.read_file(BOUNDARIES_PATH)
    return _boundaries_gdf


def pixel_to_lonlat(center_lat: float, center_lon: float, image_w: int, image_h: int, px: float, py: float):
    """Very simple prototype projection: image center = (center_lat, center_lon),
    offsets scaled by _PX_PER_DEGREE. Clearly a placeholder — swap for real
    georeferencing (EXIF GPS + camera model) beyond the prototype stage."""
    dx = (px - image_w / 2) / _PX_PER_DEGREE
    dy = (py - image_h / 2) / _PX_PER_DEGREE
    return center_lon + dx, center_lat - dy


def analyze_point(lon: float, lat: float) -> dict:
    gdf = load_boundaries()
    pt = Point(lon, lat)
    inside = False
    min_dist_deg = None
    matched_name = None
    for _, row in gdf.iterrows():
        geom = row.geometry
        if geom.contains(pt):
            inside = True
            matched_name = row.get("name", "unnamed_zone")
            min_dist_deg = 0.0
            break
        d = geom.distance(pt)
        if min_dist_deg is None or d < min_dist_deg:
            min_dist_deg = d
            matched_name = row.get("name", "unnamed_zone")

    # Rough degrees->pixels conversion using the same prototype scale, just
    # for display purposes (NOT a geodesically correct distance).
    distance_px = (min_dist_deg or 0.0) * _PX_PER_DEGREE
    return {
        "inside_boundary": inside,
        "zone_name": matched_name,
        "distance_to_boundary_px": round(distance_px, 1),
    }