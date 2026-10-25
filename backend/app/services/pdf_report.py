"""
AeroSentinel evidence report generator.

The report clearly identifies:
- user vs drone source
- CDAC YOLO model
- confidence
- location
- priority
- evidence image when available
"""

import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image as ReportImage,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.config import REPORTS_DIR


def generate_case_report(
    case_change: dict,
    report_id: str,
) -> str:

    path = os.path.join(
        REPORTS_DIR,
        f"{report_id}.pdf",
    )


    doc = SimpleDocTemplate(
        path,
        pagesize=A4,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )


    styles = (
        getSampleStyleSheet()
    )

    story = []


    # ------------------------------------------------------------
    # Title
    # ------------------------------------------------------------

    story.append(
        Paragraph(
            "AeroSentinel — Change Evidence Report",
            styles["Title"],
        )
    )


    story.append(
        Paragraph(
            "Prototype demonstration report",
            styles["Italic"],
        )
    )


    story.append(
        Spacer(
            1,
            8 * mm,
        )
    )


    # ------------------------------------------------------------
    # Basic information
    # ------------------------------------------------------------

    source = case_change.get(
        "source",
        "user",
    )

    source_label = case_change.get(
        "source_label",
        "User Report",
    )


    model = case_change.get(
        "model",
        "N/A",
    )


    generated = (
        datetime.utcnow()
        .isoformat()
        + "Z"
    )


    story.append(
        Paragraph(
            f"Generated: {generated}",
            styles["Normal"],
        )
    )


    story.append(
        Paragraph(
            f"Change ID: {case_change.get('id')}",
            styles["Normal"],
        )
    )


    story.append(
        Spacer(
            1,
            5 * mm,
        )
    )


    # ------------------------------------------------------------
    # Main table
    # ------------------------------------------------------------

    data = [

        [
            "Source",
            source_label,
        ],

        [
            "Detection model",
            model,
        ],

        [
            "Class",
            case_change.get(
                "class_name"
            ),
        ],

        [
            "Change type",
            case_change.get(
                "change_type"
            ),
        ],

        [
            "Average confidence",
            f"{case_change.get('avg_confidence', 0) * 100:.1f}%",
        ],

        [
            "Priority score",
            f"{case_change.get('priority_score', 0)} / 100",
        ],

        [
            "Latitude",
            str(
                case_change.get(
                    "lat",
                    "N/A",
                )
            ),
        ],

        [
            "Longitude",
            str(
                case_change.get(
                    "lon",
                    "N/A",
                )
            ),
        ],

        [
            "Zone",
            case_change.get(
                "zone_name",
                "unassigned",
            ),
        ],

        [
            "Inside monitored zone",
            str(
                case_change.get(
                    "inside_boundary",
                    False,
                )
            ),
        ],
    ]


    table = Table(
        data,
        colWidths=[
            60 * mm,
            100 * mm,
        ],
    )


    table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey,
                ),

                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.whitesmoke,
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
            ]
        )
    )


    story.append(table)


    story.append(
        Spacer(
            1,
            8 * mm,
        )
    )


    # ------------------------------------------------------------
    # Evidence image
    # ------------------------------------------------------------

    evidence_path = case_change.get(
        "evidence_path"
    )


    if (
        evidence_path
        and os.path.exists(
            evidence_path
        )
    ):

        story.append(
            Paragraph(
                "Detection Evidence",
                styles["Heading3"],
            )
        )


        try:

            evidence_image = ReportImage(
                evidence_path,
                width=150 * mm,
                height=84 * mm,
                kind="proportional",
            )

            story.append(
                evidence_image
            )

            story.append(
                Spacer(
                    1,
                    5 * mm,
                )
            )

        except Exception as exc:

            story.append(
                Paragraph(
                    f"Evidence image could not be embedded: {exc}",
                    styles["Normal"],
                )
            )


    # ------------------------------------------------------------
    # Priority reasoning
    # ------------------------------------------------------------

    story.append(
        Paragraph(
            "Priority Score Reasoning",
            styles["Heading3"],
        )
    )


    reasons = case_change.get(
        "priority_reasons",
        [],
    )


    if not reasons:

        story.append(
            Paragraph(
                "No priority reasoning available.",
                styles["Normal"],
            )
        )

    else:

        for reason in reasons:

            story.append(
                Paragraph(
                    f"• {reason}",
                    styles["Normal"],
                )
            )


    story.append(
        Spacer(
            1,
            8 * mm,
        )
    )


    # ------------------------------------------------------------
    # Prototype notices
    # ------------------------------------------------------------

    story.append(
        Paragraph(
            "Prototype / Data Provenance",
            styles["Heading3"],
        )
    )


    notices = []


    if source == "drone":

        notices.append(
            "This case was automatically generated by the AeroSentinel drone monitoring pipeline."
        )

        notices.append(
            "The prototype uses the laptop webcam as the drone camera source."
        )


    if model == "CDAC YOLO":

        notices.append(
            "Detection was performed using the supplied CDAC-trained YOLO weights."
        )


    if case_change.get("mock"):

        notices.append(
            "WARNING: This detection used the prototype MOCK detector because the real model weights were unavailable."
        )


    notices.append(
        "GPS coordinates are prototype/demo coordinates and should not be treated as live drone telemetry."
    )


    notices.append(
        "Priority weights are configurable prototype rules and are not scientifically validated."
    )


    for notice in notices:

        story.append(
            Paragraph(
                f"• {notice}",
                styles["Normal"],
            )
        )


    doc.build(story)

    return path