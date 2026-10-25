"""
Priority scoring engine.

Produces a 0-100 score plus a human-readable list of reasons. Every weight
used is pulled from app.config.PRIORITY_WEIGHTS and a SNAPSHOT of those
weights is attached to the result, so a score is always reproducible even
if weights are tuned later. These weights are configurable prototype rules,
not a scientifically validated risk model — say so in the UI.
"""

import copy

from app.config import PRIORITY_WEIGHTS


def score_change(change: dict, geo: dict) -> tuple[float, list[str], dict]:
    weights = copy.deepcopy(PRIORITY_WEIGHTS)
    reasons = []
    score = 0.0

    base = weights["change_type_base"].get(change["change_type"], 0)
    score += base
    reasons.append(f"Base weight for change type '{change['change_type']}': +{base}")

    conf_component = change["avg_confidence"] * weights["confidence_multiplier"]
    score += conf_component
    reasons.append(
        f"Detection confidence {change['avg_confidence']:.2f} x "
        f"{weights['confidence_multiplier']} multiplier: +{conf_component:.1f}"
    )

    if geo["inside_boundary"]:
        score += weights["boundary_inside_bonus"]
        reasons.append(
            f"Change located inside monitored zone '{geo['zone_name']}': "
            f"+{weights['boundary_inside_bonus']}"
        )
    else:
        penalty = (geo["distance_to_boundary_px"] / 100.0) * weights[
            "boundary_distance_penalty_per_100px"
        ]
        penalty = min(penalty, base)  # never let distance alone zero out a real change
        score -= penalty
        reasons.append(
            f"Change is {geo['distance_to_boundary_px']:.0f}px outside nearest "
            f"zone '{geo['zone_name']}': -{penalty:.1f}"
        )

    recurrence = max(0, change.get("num_surveys_present", 1) - 1)
    if recurrence > 0:
        bonus = recurrence * weights["recurrence_bonus_per_survey"]
        score += bonus
        reasons.append(
            f"Present across {change['num_surveys_present']} surveys (recurrence bonus): +{bonus}"
        )

    if change.get("alignment_uncertain"):
        reasons.append(
            "NOTE: image alignment between surveys was uncertain for this change — "
            "treat the classification with extra caution."
        )
    if change.get("mock"):
        reasons.append(
            "NOTE: based on MOCK detections (no real trained model weights loaded) — "
            "for architecture demonstration only, not a real finding."
        )

    score = max(0.0, min(weights["max_score"], round(score, 1)))
    return score, reasons, weights