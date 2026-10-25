from typing import Literal, Optional

from pydantic import BaseModel, Field


class BoundingBox(BaseModel):

    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def cx(self) -> float:
        return (
            self.x1 + self.x2
        ) / 2

    @property
    def cy(self) -> float:
        return (
            self.y1 + self.y2
        ) / 2


class Detection(BaseModel):

    id: str
    survey_id: str
    class_name: str
    confidence: float
    bbox: BoundingBox

    mock: bool = Field(
        default=False,
        description="True when the prototype mock detector was used.",
    )

    source: str = Field(
        default="user",
        description="Detection source: user, survey or drone.",
    )


class Survey(BaseModel):

    id: str
    label: str
    filename: str
    image_path: str
    uploaded_at: str

    lat: Optional[float] = None
    lon: Optional[float] = None

    detections_run: bool = False

    source: str = Field(
        default="survey",
        description="survey or drone",
    )


ChangeType = Literal[
    "NEW",
    "REMOVED",
    "PERSISTENT",
    "CHANGED",
]


class ChangeRecord(BaseModel):

    id: str

    class_name: str

    change_type: ChangeType

    survey_ids: list[str]

    detection_ids: list[str]

    centroid_px: tuple[
        float,
        float,
    ]

    avg_confidence: float

    inside_boundary: bool = False

    distance_to_boundary_px: float = 0.0

    priority_score: Optional[
        float
    ] = None

    priority_reasons: list[str] = (
        Field(
            default_factory=list
        )
    )

    weights_snapshot: Optional[
        dict
    ] = None

    source: str = "user"

    source_label: str = "User Report"

    model: Optional[str] = None

    lat: Optional[float] = None

    lon: Optional[float] = None

    evidence_path: Optional[str] = None