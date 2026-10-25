"""
Temporal matching engine.

Matches detections of the SAME class across an ordered list of surveys
using aligned centroid distance + a simple greedy nearest-neighbour
assignment (documented limitation: not a full Hungarian/optimal assignment,
which is fine for a prototype with a handful of detections per image, but
should be upgraded before scaling to dense scenes).

Detections are first warped into the reference survey's coordinate frame
via app.services.alignment, so matching is done in a common frame instead
of raw per-image pixels.
"""

import math

from app.config import MATCH_DISTANCE_THRESHOLD_PX
from app.services.alignment import compute_homography, warp_point


def _dist(a, b) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _threshold_for(class_name: str) -> float:
    return MATCH_DISTANCE_THRESHOLD_PX.get(class_name, MATCH_DISTANCE_THRESHOLD_PX["default"])


def build_change_records(surveys: list[dict], detections_by_survey: dict[str, list[dict]]) -> list[dict]:
    """
    surveys: ordered list of survey dicts (chronological), each with 'id' and 'image_path'.
    detections_by_survey: {survey_id: [detection dict, ...]}

    Returns a list of change-record dicts (not yet scored for priority).
    """
    if not surveys:
        return []

    reference = surveys[0]
    ref_path = reference["image_path"]

    # Warp every non-reference survey's detection centroids into the reference frame.
    warped_points: dict[str, list[dict]] = {reference["id"]: []}
    for det in detections_by_survey.get(reference["id"], []):
        cx = (det["bbox"]["x1"] + det["bbox"]["x2"]) / 2
        cy = (det["bbox"]["y1"] + det["bbox"]["y2"]) / 2
        warped_points[reference["id"]].append({**det, "warped_xy": (cx, cy), "aligned": True})

    alignment_flags: dict[str, bool] = {reference["id"]: True}

    for survey in surveys[1:]:
        H, aligned = compute_homography(ref_path, survey["image_path"])
        alignment_flags[survey["id"]] = aligned
        pts = []
        for det in detections_by_survey.get(survey["id"], []):
            cx = (det["bbox"]["x1"] + det["bbox"]["x2"]) / 2
            cy = (det["bbox"]["y1"] + det["bbox"]["y2"]) / 2
            wx, wy = warp_point(H, cx, cy)
            pts.append({**det, "warped_xy": (wx, wy), "aligned": aligned})
        warped_points[survey["id"]] = pts

    # Greedy chain-matching: start from reference detections, try to find a
    # match in each subsequent survey (same class, nearest centroid within threshold).
    used = {sid: set() for sid in warped_points}
    chains = []

    def find_match(survey_id, class_name, xy):
        best_idx, best_d = None, None
        for idx, det in enumerate(warped_points[survey_id]):
            if idx in used[survey_id] or det["class_name"] != class_name:
                continue
            d = _dist(xy, det["warped_xy"])
            if d <= _threshold_for(class_name) and (best_d is None or d < best_d):
                best_idx, best_d = idx, d
        return best_idx

    survey_ids = [s["id"] for s in surveys]

    # Start chains from every unused detection in every survey (in order),
    # so objects that first appear in a later survey (NEW) are also captured.
    for start_i, start_sid in enumerate(survey_ids):
        for idx, det in enumerate(warped_points[start_sid]):
            if idx in used[start_sid]:
                continue
            chain = {start_sid: idx}
            used[start_sid].add(idx)
            cursor_xy = det["warped_xy"]
            for next_sid in survey_ids[start_i + 1 :]:
                match_idx = find_match(next_sid, det["class_name"], cursor_xy)
                if match_idx is not None:
                    chain[next_sid] = match_idx
                    used[next_sid].add(match_idx)
                    cursor_xy = warped_points[next_sid][match_idx]["warped_xy"]
                else:
                    break
            chains.append({"class_name": det["class_name"], "chain": chain, "start_i": start_i})

    change_records = []
    n_surveys = len(survey_ids)
    for c in chains:
        chain = c["chain"]
        present_indices = sorted(survey_ids.index(sid) for sid in chain)
        first_i, last_i = present_indices[0], present_indices[-1]

        if first_i == 0 and last_i == n_surveys - 1 and len(present_indices) == n_surveys:
            change_type = "PERSISTENT"
        elif first_i > 0 and last_i == n_surveys - 1:
            change_type = "NEW"
        elif first_i == 0 and last_i < n_surveys - 1:
            change_type = "REMOVED"
        else:
            change_type = "CHANGED"

        dets = []
        xys = []
        for sid, idx in chain.items():
            d = warped_points[sid][idx]
            dets.append(d)
            xys.append(d["warped_xy"])
        avg_x = sum(p[0] for p in xys) / len(xys)
        avg_y = sum(p[1] for p in xys) / len(xys)
        avg_conf = sum(d["confidence"] for d in dets) / len(dets)
        any_mock = any(d.get("mock") for d in dets)
        any_misaligned = any(not warped_points[sid][idx].get("aligned", True) for sid, idx in chain.items())

        change_records.append(
            {
                "class_name": c["class_name"],
                "change_type": change_type,
                "survey_ids": list(chain.keys()),
                "detection_ids": [d.get("id") for d in dets],
                "centroid_px": (avg_x, avg_y),
                "avg_confidence": avg_conf,
                "num_surveys_present": len(present_indices),
                "mock": any_mock,
                "alignment_uncertain": any_misaligned,
            }
        )

    return change_records