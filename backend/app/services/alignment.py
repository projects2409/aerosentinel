"""
Image registration / alignment.

Computes a homography from a later survey image back onto the reference
(first) survey using ORB features + RANSAC, and exposes a helper to warp
detection bounding boxes through that homography so temporal matching
compares apples to apples across surveys instead of raw per-image pixels.

If alignment fails (too few matches, degenerate homography), we fall back
to the identity transform and flag `aligned=False`.
"""

import cv2
import numpy as np


def compute_homography(reference_path: str, target_path: str):
    """Returns (H, aligned: bool). H maps target-image coords -> reference-image coords."""
    ref = cv2.imread(reference_path, cv2.IMREAD_GRAYSCALE)
    tgt = cv2.imread(target_path, cv2.IMREAD_GRAYSCALE)
    if ref is None or tgt is None:
        return np.eye(3), False

    orb = cv2.ORB_create(2000)
    kp1, des1 = orb.detectAndCompute(ref, None)
    kp2, des2 = orb.detectAndCompute(tgt, None)
    if des1 is None or des2 is None or len(kp1) < 10 or len(kp2) < 10:
        return np.eye(3), False

    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(des1, des2)
    matches = sorted(matches, key=lambda m: m.distance)
    if len(matches) < 15:
        return np.eye(3), False

    good = matches[: max(15, int(len(matches) * 0.3))]
    src_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)

    H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
    if H is None:
        return np.eye(3), False
    inliers = int(mask.sum()) if mask is not None else 0
    if inliers < 10:
        return H, False
    return H, True


def warp_point(H: np.ndarray, x: float, y: float) -> tuple[float, float]:
    pt = np.array([x, y, 1.0])
    warped = H @ pt
    if warped[2] == 0:
        return x, y
    return float(warped[0] / warped[2]), float(warped[1] / warped[2])