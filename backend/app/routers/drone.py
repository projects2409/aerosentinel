"""
AeroSentinel Drone Monitoring Router

Prototype flow:

Laptop webcam
      ↓
Frame
      ↓
CDAC YOLO (best.pt)
      ↓
YOLO detections + bounding boxes
      ↓
Compare with previous frame
      ↓
Change detected
      ↓
Save evidence image
      ↓
Create change record
      ↓
Calculate priority
      ↓
Generate PDF report automatically
      ↓
Store report in existing Reports collection
"""

import io
import os
import time

import cv2

from fastapi import (
    APIRouter,
    File,
    HTTPException,
    UploadFile,
)
from PIL import Image

from app import storage
from app.config import UPLOADS_DIR
from app.services.geospatial import (
    analyze_point,
    pixel_to_lonlat,
)
from app.services.pdf_report import (
    generate_case_report,
)
from app.services.priority_engine import (
    score_change,
)
from app.services.yolo_service import (
    is_mock_mode,
    model_info,
    run_detection_bytes,
)


router = APIRouter(
    prefix="/api/drone",
    tags=["drone"],
)


# ============================================================
# DRONE PROTOTYPE CONFIGURATION
# ============================================================

# Prototype GPS position.
# This represents the approximate drone operating area.
DRONE_LAT = 29.863
DRONE_LON = 77.875


# Don't generate a new report for every frame.
MIN_REPORT_INTERVAL_SECONDS = 5


# Keep track of the last automatic report.
_last_report_time = 0.0


# ============================================================
# DRONE STATUS
# ============================================================

@router.get("/status")
async def drone_status():
    return {
        "online": True,
        "monitoring": True,
        "source": "laptop_webcam",
        "source_label": "Drone Camera Prototype",
        "model": (
            "CDAC YOLO"
            if not is_mock_mode()
            else "MOCK"
        ),
        "mock_mode": is_mock_mode(),
    }


# ============================================================
# DRONE MODEL
# ============================================================

@router.get("/model")
async def drone_model():
    return model_info()


# ============================================================
# PROCESS LIVE WEBCAM FRAME
# ============================================================

@router.post("/detect")
async def detect_drone_frame(
    file: UploadFile = File(...)
):
    global _last_report_time

    # --------------------------------------------------------
    # Read webcam image
    # --------------------------------------------------------

    image_bytes = await file.read()

    if not image_bytes:
        raise HTTPException(
            status_code=400,
            detail="Empty webcam frame",
        )

    # --------------------------------------------------------
    # Run CDAC YOLO
    # --------------------------------------------------------

    detections = run_detection_bytes(
        image_bytes
    )

    # --------------------------------------------------------
    # Get image dimensions
    # --------------------------------------------------------

    try:
        image = Image.open(
            io.BytesIO(
                image_bytes
            )
        )

        width, height = image.size

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid image: {exc}",
        )

    # --------------------------------------------------------
    # Get previous drone state
    # --------------------------------------------------------

    previous_state = storage.get(
        "drone_state",
        "current",
    )

    # IMPORTANT:
    # Do NOT use "if not previous_detections"
    # to determine whether a baseline exists.
    #
    # An empty first frame is still a valid baseline.
    # --------------------------------------------------------

    baseline_initialized = False

    previous_detections = []

    if previous_state:

        baseline_initialized = bool(
            previous_state.get(
                "baseline_initialized",
                False,
            )
        )

        previous_detections = (
            previous_state.get(
                "detections",
                [],
            )
        )

    # ========================================================
    # FIRST FRAME = BASELINE
    # ========================================================

    if not baseline_initialized:

        storage.put(
            "drone_state",
            "current",
            {
                "id": "current",

                "detections":
                    _serialise_detections(
                        detections
                    ),

                "baseline_initialized":
                    True,

                "updated_at":
                    storage.now_iso(),
            },
        )

        return {
            "status":
                "baseline_created",

            "change_detected":
                False,

            "report_created":
                False,

            "detections":
                detections,

            "count":
                len(detections),

            "mock_mode":
                is_mock_mode(),

            "source":
                "drone",

            "source_label":
                "Drone / CDAC YOLO",

            "message":
                (
                    "Initial drone frame "
                    "stored as baseline."
                ),
        }

    # ========================================================
    # COMPARE CURRENT FRAME WITH BASELINE
    # ========================================================

    changed = _detect_change(
        previous_detections,
        detections,
    )

    # --------------------------------------------------------
    # Store current frame for next comparison
    # --------------------------------------------------------

    storage.put(
        "drone_state",
        "current",
        {
            "id": "current",

            "detections":
                _serialise_detections(
                    detections
                ),

            "baseline_initialized":
                True,

            "updated_at":
                storage.now_iso(),
        },
    )

    # ========================================================
    # NO CHANGE
    # ========================================================

    if not changed:

        return {
            "status":
                "monitoring",

            "change_detected":
                False,

            "report_created":
                False,

            "detections":
                detections,

            "count":
                len(detections),

            "mock_mode":
                is_mock_mode(),

            "source":
                "drone",

            "source_label":
                "Drone / CDAC YOLO",
        }

    # ========================================================
    # CHANGE DETECTED
    # ========================================================

    now = time.time()

    # --------------------------------------------------------
    # Prevent report spam
    # --------------------------------------------------------

    if (
        now - _last_report_time
        < MIN_REPORT_INTERVAL_SECONDS
    ):

        return {
            "status":
                "change_detected",

            "change_detected":
                True,

            "report_created":
                False,

            "detections":
                detections,

            "count":
                len(detections),

            "mock_mode":
                is_mock_mode(),

            "source":
                "drone",

            "source_label":
                "Drone / CDAC YOLO",

            "message":
                (
                    "Change detected. "
                    "Report cooldown is active."
                ),
        }

    _last_report_time = now

    # ========================================================
    # SAVE EVIDENCE FRAME
    # ========================================================

    evidence_id = storage.new_id(
        "drone_"
    )

    evidence_filename = (
        f"{evidence_id}.jpg"
    )

    evidence_path = os.path.join(
        UPLOADS_DIR,
        evidence_filename,
    )

    # --------------------------------------------------------
    # Create an annotated evidence image.
    #
    # This is NOT the live-feed overlay.
    # The frontend will draw the live box separately.
    #
    # This creates a saved evidence image with the
    # AI bounding box.
    # --------------------------------------------------------

    try:

        image_array = cv2.imdecode(
            __import__("numpy").frombuffer(
                image_bytes,
                dtype=__import__(
                    "numpy"
                ).uint8,
            ),
            cv2.IMREAD_COLOR,
        )

        if image_array is not None:

            for detection in detections:

                bbox = detection[
                    "bbox"
                ]

                if hasattr(
                    bbox,
                    "model_dump",
                ):
                    bbox = bbox.model_dump()

                x1 = int(
                    bbox["x1"]
                )

                y1 = int(
                    bbox["y1"]
                )

                x2 = int(
                    bbox["x2"]
                )

                y2 = int(
                    bbox["y2"]
                )

                confidence = float(
                    detection[
                        "confidence"
                    ]
                )

                # Green detection box
                cv2.rectangle(
                    image_array,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    3,
                )

                # Do NOT expose the underlying
                # YOLO class in the prototype UI.
                label = (
                    "AI ANALYSIS "
                    f"{confidence * 100:.1f}%"
                )

                label_y = max(
                    25,
                    y1 - 10,
                )

                cv2.putText(
                    image_array,
                    label,
                    (
                        x1,
                        label_y,
                    ),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2,
                    cv2.LINE_AA,
                )

            cv2.imwrite(
                evidence_path,
                image_array,
            )

        else:

            with open(
                evidence_path,
                "wb",
            ) as out:
                out.write(
                    image_bytes
                )

    except Exception:

        # If annotation fails,
        # still preserve the original
        # evidence frame.
        with open(
            evidence_path,
            "wb",
        ) as out:
            out.write(
                image_bytes
            )

    # ========================================================
    # CREATE SURVEY RECORD
    # ========================================================

    survey_id = storage.new_id(
        "drone_survey_"
    )

    survey = {
        "id":
            survey_id,

        "label":
            "DRONE",

        "filename":
            evidence_filename,

        "image_path":
            evidence_path,

        "uploaded_at":
            storage.now_iso(),

        "lat":
            DRONE_LAT,

        "lon":
            DRONE_LON,

        "detections_run":
            True,

        "source":
            "drone",
    }

    storage.put(
        "surveys",
        survey_id,
        survey,
    )

    # ========================================================
    # STORE DETECTIONS
    # ========================================================

    stored_detections = []

    for detection in detections:

        det_id = storage.new_id(
            "drone_det_"
        )

        bbox = detection[
            "bbox"
        ]

        if hasattr(
            bbox,
            "model_dump",
        ):
            bbox = bbox.model_dump()

        record = {
            "id":
                det_id,

            "survey_id":
                survey_id,

            "class_name":
                detection[
                    "class_name"
                ],

            "confidence":
                detection[
                    "confidence"
                ],

            "bbox":
                bbox,

            "mock":
                detection[
                    "mock"
                ],

            "source":
                "drone",
        }

        storage.put(
            "detections",
            det_id,
            record,
        )

        stored_detections.append(
            record
        )

    # ========================================================
    # SELECT STRONGEST DETECTION
    # ========================================================

    if not stored_detections:

        return {
            "status":
                "change_detected",

            "change_detected":
                True,

            "report_created":
                False,

            "detections":
                detections,

            "count":
                0,

            "mock_mode":
                is_mock_mode(),

            "message":
                (
                    "A change condition was "
                    "detected, but no current "
                    "detection is available "
                    "for report generation."
                ),
        }

    strongest = max(
        stored_detections,
        key=lambda d:
            d["confidence"],
    )

    bbox = strongest[
        "bbox"
    ]

    # ========================================================
    # CENTROID
    # ========================================================

    centroid = (
        (
            bbox["x1"]
            + bbox["x2"]
        )
        / 2,

        (
            bbox["y1"]
            + bbox["y2"]
        )
        / 2,
    )

    # ========================================================
    # PIXEL → APPROXIMATE GPS
    # ========================================================

    lon, lat = pixel_to_lonlat(
        DRONE_LAT,
        DRONE_LON,
        width,
        height,
        centroid[0],
        centroid[1],
    )

    geo = analyze_point(
        lon,
        lat,
    )

    # ========================================================
    # CREATE CHANGE RECORD
    # ========================================================

    change_id = storage.new_id(
        "change_"
    )

    change = {
        "id":
            change_id,

        "class_name":
            strongest[
                "class_name"
            ],

        "change_type":
            "CHANGED",

        "survey_ids":
            [
                survey_id
            ],

        "detection_ids":
            [
                d["id"]
                for d
                in stored_detections
            ],

        "centroid_px":
            centroid,

        "avg_confidence":
            strongest[
                "confidence"
            ],

        "num_surveys_present":
            1,

        "mock":
            strongest[
                "mock"
            ],

        "alignment_uncertain":
            False,

        # ----------------------------------------------------
        # Drone metadata
        # ----------------------------------------------------

        "source":
            "drone",

        "source_label":
            "Drone / CDAC YOLO",

        "model":
            (
                "MOCK"
                if strongest[
                    "mock"
                ]
                else "CDAC YOLO"
            ),

        "evidence_path":
            evidence_path,

        "evidence_filename":
            evidence_filename,

        # ----------------------------------------------------
        # Location
        # ----------------------------------------------------

        "lat":
            lat,

        "lon":
            lon,

        "inside_boundary":
            geo[
                "inside_boundary"
            ],

        "distance_to_boundary_px":
            geo[
                "distance_to_boundary_px"
            ],

        "zone_name":
            geo[
                "zone_name"
            ],
    }

    storage.put(
        "changes",
        change_id,
        change,
    )

    # ========================================================
    # AUTOMATIC PRIORITY
    # ========================================================

    score, reasons, weights = (
        score_change(
            change,
            geo,
        )
    )

    change = storage.update(
        "changes",
        change_id,
        {
            "priority_score":
                score,

            "priority_reasons":
                reasons,

            "weights_snapshot":
                weights,
        },
    )

    # ========================================================
    # AUTOMATIC PDF REPORT
    # ========================================================

    report_id = storage.new_id(
        "report_"
    )

    report_path = (
        generate_case_report(
            change,
            report_id,
        )
    )

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # This stores the report in the SAME
    # "reports" collection used by:
    #
    # GET /api/reports/list
    #
    # Therefore it automatically appears
    # in the existing Reports section.
    # --------------------------------------------------------

    storage.put(
        "reports",
        report_id,
        {
            "id":
                report_id,

            "change_id":
                change_id,

            "path":
                report_path,

            "created_at":
                storage.now_iso(),

            "source":
                "drone",

            "source_label":
                "Drone / CDAC YOLO",

            "title":
                "AI-Detected Change Report",

            "evidence_path":
                evidence_path,

            "evidence_filename":
                evidence_filename,

            "lat":
                lat,

            "lon":
                lon,

            "priority_score":
                score,
        },
    )

    # ========================================================
    # RETURN RESULT TO FRONTEND
    # ========================================================

    return {
        "status":
            "report_created",

        "change_detected":
            True,

        "report_created":
            True,

        "change_id":
            change_id,

        "report_id":
            report_id,

        "report_url":
            (
                f"/api/reports/download/"
                f"{report_id}"
            ),

        "detections":
            detections,

        "count":
            len(detections),

        # Internally available.
        # The frontend should not display
        # the class name to the professor.
        "class_name":
            strongest[
                "class_name"
            ],

        "confidence":
            strongest[
                "confidence"
            ],

        "priority_score":
            score,

        "lat":
            lat,

        "lon":
            lon,

        "source":
            "drone",

        "source_label":
            "Drone / CDAC YOLO",

        "model":
            (
                "MOCK"
                if strongest[
                    "mock"
                ]
                else "CDAC YOLO"
            ),

        "evidence_filename":
            evidence_filename,

        "mock_mode":
            is_mock_mode(),

        "message":
            (
                "AI-detected change. "
                "Evidence captured and "
                "report generated automatically."
            ),
    }


# ============================================================
# SERIALISE DETECTIONS
# ============================================================

def _serialise_detections(
    detections: list[dict],
) -> list[dict]:

    output = []

    for detection in detections:

        bbox = detection[
            "bbox"
        ]

        if hasattr(
            bbox,
            "model_dump",
        ):
            bbox = bbox.model_dump()

        output.append(
            {
                "class_name":
                    detection[
                        "class_name"
                    ],

                "confidence":
                    detection[
                        "confidence"
                    ],

                "bbox":
                    bbox,

                "mock":
                    detection.get(
                        "mock",
                        False,
                    ),
            }
        )

    return output


# ============================================================
# BOUNDING BOX CENTRE
# ============================================================

def _centre(detection):
    """
    Return the centre point of a detection bounding box.

    The detection produced by YOLO has this structure:

    {
        "class_name": "person",
        "confidence": 0.72,
        "bbox": BoundingBox(...),
        "mock": False
    }
    """

    # If the caller passed the complete detection dictionary,
    # extract the actual BoundingBox object first.
    if isinstance(detection, dict) and "bbox" in detection:
        bbox = detection["bbox"]
    else:
        bbox = detection

    # Ultralytics BoundingBox object
    if hasattr(bbox, "x1"):
        return (
            (float(bbox.x1) + float(bbox.x2)) / 2,
            (float(bbox.y1) + float(bbox.y2)) / 2,
        )

    # Dictionary containing x1/y1/x2/y2
    if isinstance(bbox, dict):
        if all(k in bbox for k in ("x1", "y1", "x2", "y2")):
            return (
                (float(bbox["x1"]) + float(bbox["x2"])) / 2,
                (float(bbox["y1"]) + float(bbox["y2"])) / 2,
            )

        # Dictionary containing xyxy
        if "xyxy" in bbox:
            coords = bbox["xyxy"]

            if hasattr(coords, "tolist"):
                coords = coords.tolist()

            if coords and isinstance(coords[0], (list, tuple)):
                coords = coords[0]

            if len(coords) >= 4:
                x1, y1, x2, y2 = map(float, coords[:4])
                return (
                    (x1 + x2) / 2,
                    (y1 + y2) / 2,
                )

    raise ValueError(f"Unsupported bounding box format: {bbox}")

# ============================================================
# DISTANCE BETWEEN TWO CENTRES
# ============================================================

def _distance(
    a,
    b,
):
    dx = a[0] - b[0]
    dy = a[1] - b[1]

    return (
        dx * dx
        + dy * dy
    ) ** 0.5


# ============================================================
# CHANGE DETECTION
# ============================================================

def _detect_change(
    previous,
    current,
):
    """
    Simple prototype temporal change detector.

    A change is detected when:

    1. A new detection appears.
    2. A previous detection disappears.
    3. A detection moves more than the threshold.

    The model class is still used internally
    for matching, but the frontend can present
    the result simply as "AI-Detected Change".
    """

    MOVEMENT_THRESHOLD = 100

    # --------------------------------------------------------
    # No previous detections
    # --------------------------------------------------------

    if not previous:

        # If something appears in the
        # current frame, that's a change.
        if current:
            return True

        return False

    # --------------------------------------------------------
    # Previous detections exist,
    # current frame is empty.
    # --------------------------------------------------------

    if not current:
        return True

    # --------------------------------------------------------
    # Look for every current detection
    # in the previous frame.
    # --------------------------------------------------------

    for current_detection in current:

        best_distance = None

        for previous_detection in previous:

            # Same YOLO class only.
            if (
                current_detection[
                    "class_name"
                ]
                != previous_detection[
                    "class_name"
                ]
            ):
                continue

            distance = _distance(
                _centre(
                    current_detection
                ),
                _centre(
                    previous_detection
                ),
            )

            if (
                best_distance is None
                or distance < best_distance
            ):
                best_distance = distance

        # ----------------------------------------------------
        # New object
        # ----------------------------------------------------

        if best_distance is None:
            return True

        # ----------------------------------------------------
        # Significant movement
        # ----------------------------------------------------

        if (
            best_distance
            > MOVEMENT_THRESHOLD
        ):
            return True

    # --------------------------------------------------------
    # Detect an object that disappeared.
    # --------------------------------------------------------

    for previous_detection in previous:

        best_distance = None

        for current_detection in current:

            if (
                current_detection[
                    "class_name"
                ]
                != previous_detection[
                    "class_name"
                ]
            ):
                continue

            distance = _distance(
                _centre(
                    previous_detection
                ),
                _centre(
                    current_detection
                ),
            )

            if (
                best_distance is None
                or distance < best_distance
            ):
                best_distance = distance

        if best_distance is None:
            return True

    return False