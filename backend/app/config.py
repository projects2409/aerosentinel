"""
Central configuration for AeroSentinel prototype.

All "risk weight" / threshold values here are DELIBERATELY simple and
configurable. They are NOT scientifically validated — they exist so the
priority engine has something explainable to reason over. Treat every
number in PRIORITY_WEIGHTS as a prototype default you can tune live.
"""

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "app", "data")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")
SURVEYS_DIR = os.path.join(DATA_DIR, "surveys")
REPORTS_DIR = os.path.join(DATA_DIR, "reports")

# <<< EDIT THIS if your CADC weight file has a different name or lives
# somewhere else, e.g.:
# WEIGHTS_PATH = os.path.join(BASE_DIR, "weights", "cadc_person_detector.pt")
WEIGHTS_PATH = os.path.join(BASE_DIR, "weights", "best.pt")

# Only used when a real model (e.g. your CADC-trained weights) is loaded.
# Detections below this confidence are discarded before they ever reach
# matching/scoring. Tune this per your model — CADC's person/victim model
# may need a different threshold than whatever it was validated at.
YOLO_CONFIDENCE_THRESHOLD = 0.25

# "cpu", "cuda:0", or "mps" (Apple Silicon). "cpu" is the safe default for a
# classroom demo on a laptop with no dedicated GPU/CUDA setup.
YOLO_DEVICE = "cpu"

BOUNDARIES_PATH = os.path.join(
    os.path.dirname(BASE_DIR), "sample_data", "boundaries.geojson"
)

for d in (UPLOADS_DIR, SURVEYS_DIR, REPORTS_DIR):
    os.makedirs(d, exist_ok=True)

# Matching: max centroid distance (in pixels, post-alignment) for two
# detections of the SAME class across surveys to be considered the same
# real-world object. This is a naive heuristic for the prototype — a
# production system would use georeferenced coordinates instead of pixels.
MATCH_DISTANCE_THRESHOLD_PX = {
    "default": 40,
}

# Configurable priority scoring weights (0-100 scale is assembled from these).
# NONE of these are derived from research; they are prototype defaults meant
# to be edited/tuned during demos and clearly presented as such in the UI.
PRIORITY_WEIGHTS = {
    "change_type_base": {
        "NEW": 35,
        "REMOVED": 25,
        "CHANGED": 20,
        "PERSISTENT": 5,
    },
    "confidence_multiplier": 20,       # scaled by avg detection confidence (0-1)
    "boundary_inside_bonus": 15,       # bonus if change is inside a protected/monitored polygon
    "boundary_distance_penalty_per_100px": 2,  # small penalty per 100px outside boundary
    "recurrence_bonus_per_survey": 5,  # bonus per additional survey where change persists
    "max_score": 100,
}

# CORS for local dev frontend
FRONTEND_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]