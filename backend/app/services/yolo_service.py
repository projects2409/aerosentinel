"""
YOLO detection service for AeroSentinel.

Real mode:
    Loads the supplied CDAC-trained YOLO model from:
        backend/weights/best.pt

The same model is used for:
    - uploaded survey images
    - laptop webcam / drone monitoring frames

Mock mode:
    Only used when the CDAC weights are not available.

For the prototype, we clearly expose whether detections are real or mock.
"""

import hashlib
import io
import os
import random

import cv2
import numpy as np
from PIL import Image

from app.config import WEIGHTS_PATH, YOLO_CONFIDENCE_THRESHOLD, YOLO_DEVICE
from app.schemas import BoundingBox


_MOCK_CLASSES = [
    "structure",
    "vegetation_loss",
    "debris",
    "water_body",
    "road_damage",
]

_model = None
_model_load_attempted = False


def _try_load_real_model():
    """
    Load the supplied CDAC YOLO model once.
    """

    global _model, _model_load_attempted

    if _model_load_attempted:
        return _model

    _model_load_attempted = True

    if not os.path.exists(WEIGHTS_PATH):
        return None

    try:
        from ultralytics import YOLO
    except ImportError:
        return None

    try:
        _model = YOLO(WEIGHTS_PATH)
        return _model
    except Exception as exc:
        print(f"[YOLO] Failed to load model: {exc}")
        return None


def is_mock_mode() -> bool:
    """
    True when the real CDAC model is unavailable.
    """

    return _try_load_real_model() is None


def model_info() -> dict:
    """
    Information shown by the frontend.
    """

    model = _try_load_real_model()

    if model is None:
        return {
            "mock_mode": True,
            "model": "MOCK",
            "weights_path": WEIGHTS_PATH,
        }

    names = getattr(model, "names", {})

    return {
        "mock_mode": False,
        "model": "CDAC YOLO",
        "weights_path": WEIGHTS_PATH,
        "classes": names,
    }


def run_detection(image_path: str) -> list[dict]:
    """
    Run YOLO on an image file.
    """

    model = _try_load_real_model()

    if model is not None:
        return _run_real(model, image_path)

    return _run_mock(image_path)


def run_detection_bytes(image_bytes: bytes) -> list[dict]:
    """
    Run YOLO directly on bytes received from the webcam/frontend.

    This is used by:
        POST /api/drone/detect
    """

    if not image_bytes:
        return []

    model = _try_load_real_model()

    if model is None:
        return _run_mock_bytes(image_bytes)

    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception as exc:
        raise ValueError(f"Could not decode webcam image: {exc}") from exc

    return _run_real_image(model, image)


def _run_real(model, image_path: str) -> list[dict]:
    """
    Real YOLO inference on an image path.
    """

    results = model(
        image_path,
        verbose=False,
        conf=YOLO_CONFIDENCE_THRESHOLD,
        device=YOLO_DEVICE,
    )

    return _format_results(results, model)


def _run_real_image(model, image) -> list[dict]:
    """
    Real YOLO inference on a PIL/OpenCV image.
    """

    results = model(
        image,
        verbose=False,
        conf=YOLO_CONFIDENCE_THRESHOLD,
        device=YOLO_DEVICE,
    )

    return _format_results(results, model)


def _format_results(results, model) -> list[dict]:
    """
    Convert Ultralytics output into our API format.
    """

    out = []

    for result in results:
        names = result.names

        if result.boxes is None:
            continue

        for box in result.boxes:
            cls_id = int(box.cls[0])
            confidence = float(box.conf[0])

            x1, y1, x2, y2 = [
                float(v) for v in box.xyxy[0]
            ]

            if isinstance(names, dict):
                class_name = names.get(cls_id, str(cls_id))
            else:
                class_name = str(names[cls_id])

            out.append(
                {
                    "class_name": class_name,
                    "confidence": confidence,
                    "bbox": BoundingBox(
                        x1=x1,
                        y1=y1,
                        x2=x2,
                        y2=y2,
                    ),
                    "mock": False,
                }
            )

    return out


def _run_mock(image_path: str) -> list[dict]:
    """
    Deterministic mock detection for development only.
    """

    img = cv2.imread(image_path)

    if img is None:
        h, w = 720, 1280
    else:
        h, w = img.shape[:2]

    with open(image_path, "rb") as f:
        digest = hashlib.sha256(f.read()).hexdigest()

    rng = random.Random(digest)

    n = rng.randint(2, 5)

    out = []

    for _ in range(n):
        bw = rng.randint(40, 120)
        bh = rng.randint(40, 120)

        x1 = rng.randint(0, max(1, w - bw))
        y1 = rng.randint(0, max(1, h - bh))

        out.append(
            {
                "class_name": rng.choice(_MOCK_CLASSES),
                "confidence": round(
                    rng.uniform(0.10, 0.95),
                    2,
                ),
                "bbox": BoundingBox(
                    x1=x1,
                    y1=y1,
                    x2=x1 + bw,
                    y2=y1 + bh,
                ),
                "mock": True,
            }
        )

    return out


def _run_mock_bytes(image_bytes: bytes) -> list[dict]:
    """
    Mock detection for webcam frames.

    This exists only so the frontend can be tested before
    the real CDAC weights are installed.
    """

    try:
        image = Image.open(
            io.BytesIO(image_bytes)
        ).convert("RGB")

        w, h = image.size
    except Exception:
        w, h = 1280, 720

    digest = hashlib.sha256(image_bytes).hexdigest()
    rng = random.Random(digest)

    n = rng.randint(1, 3)

    out = []

    for _ in range(n):
        bw = rng.randint(60, 150)
        bh = rng.randint(60, 150)

        x1 = rng.randint(0, max(1, w - bw))
        y1 = rng.randint(0, max(1, h - bh))

        out.append(
            {
                "class_name": rng.choice(_MOCK_CLASSES),
                "confidence": round(
                    rng.uniform(0.55, 0.95),
                    2,
                ),
                "bbox": BoundingBox(
                    x1=x1,
                    y1=y1,
                    x2=x1 + bw,
                    y2=y1 + bh,
                ),
                "mock": True,
            }
        )

    return out