import os
import shutil

from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    UploadFile,
)

from app import storage
from app.config import UPLOADS_DIR


router = APIRouter(
    prefix="/api/upload",
    tags=["upload"],
)


ALLOWED_EXT = {
    ".jpg",
    ".jpeg",
    ".png",
    ".tif",
    ".tiff",
}


@router.post("/survey")
async def upload_survey(
    # --------------------------------------------------------
    # CURRENT / WITH-CHANGE IMAGE
    # REQUIRED
    # --------------------------------------------------------
    file: UploadFile = File(...),

    # --------------------------------------------------------
    # SURVEY INFORMATION
    # --------------------------------------------------------
    label: str = Form(...),

    lat: float | None = Form(None),

    lon: float | None = Form(None),

    # --------------------------------------------------------
    # PREVIOUS / WITHOUT-CHANGE IMAGE
    # OPTIONAL
    # --------------------------------------------------------
    previous_file: UploadFile | None = File(None),
):
    # ========================================================
    # CHECK CURRENT IMAGE
    # ========================================================

    if not file.filename:
        raise HTTPException(
            400,
            "Current / changed image is required.",
        )

    current_ext = os.path.splitext(
        file.filename
    )[1].lower()

    if current_ext not in ALLOWED_EXT:
        raise HTTPException(
            400,
            (
                f"Unsupported current image "
                f"type '{current_ext}'. "
                f"Allowed: {sorted(ALLOWED_EXT)}"
            ),
        )

    # ========================================================
    # CHECK PREVIOUS IMAGE IF PROVIDED
    # ========================================================

    previous_ext = None

    if previous_file is not None:

        if not previous_file.filename:
            previous_file = None

        else:
            previous_ext = os.path.splitext(
                previous_file.filename
            )[1].lower()

            if previous_ext not in ALLOWED_EXT:
                raise HTTPException(
                    400,
                    (
                        f"Unsupported previous image "
                        f"type '{previous_ext}'. "
                        f"Allowed: {sorted(ALLOWED_EXT)}"
                    ),
                )

    # ========================================================
    # CREATE SURVEY ID
    # ========================================================

    survey_id = storage.new_id(
        "survey_"
    )

    # ========================================================
    # SAVE CURRENT / WITH-CHANGE IMAGE
    # ========================================================

    current_safe_name = (
        f"{survey_id}{current_ext}"
    )

    current_dest_path = os.path.join(
        UPLOADS_DIR,
        current_safe_name,
    )

    with open(
        current_dest_path,
        "wb",
    ) as out:

        shutil.copyfileobj(
            file.file,
            out,
        )

    # ========================================================
    # SAVE PREVIOUS / WITHOUT-CHANGE IMAGE
    # ========================================================

    previous_dest_path = None
    previous_safe_name = None

    if previous_file is not None:

        previous_safe_name = (
            f"{survey_id}_previous"
            f"{previous_ext}"
        )

        previous_dest_path = os.path.join(
            UPLOADS_DIR,
            previous_safe_name,
        )

        with open(
            previous_dest_path,
            "wb",
        ) as out:

            shutil.copyfileobj(
                previous_file.file,
                out,
            )

    # ========================================================
    # CREATE SURVEY RECORD
    # ========================================================

    record = {
        "id":
            survey_id,

        # Existing fields
        "label":
            label,

        "filename":
            file.filename,

        "image_path":
            current_dest_path,

        "uploaded_at":
            storage.now_iso(),

        "lat":
            lat,

        "lon":
            lon,

        "detections_run":
            False,

        # ====================================================
        # NEW FIELDS
        # ====================================================

        # Current / changed image
        "current_image_path":
            current_dest_path,

        "current_filename":
            file.filename,

        # Previous / without-change image
        # These will be None when the user
        # uploads only one image.
        "previous_image_path":
            previous_dest_path,

        "previous_filename":
            (
                previous_file.filename
                if previous_file is not None
                else None
            ),

        # Easy flag for the frontend/backend
        "has_previous_image":
            previous_file is not None,

        # Source
        "source":
            "survey",
    }

    # ========================================================
    # SAVE SURVEY
    # ========================================================

    storage.put(
        "surveys",
        survey_id,
        record,
    )

    return record


# ============================================================
# LIST SURVEYS
# ============================================================

@router.get("/surveys")
async def list_surveys():

    return sorted(
        storage.list_all(
            "surveys"
        ),
        key=lambda s:
            s["uploaded_at"],
    )


# ============================================================
# GET ONE SURVEY
# ============================================================

@router.get(
    "/surveys/{survey_id}"
)
async def get_survey(
    survey_id: str,
):

    rec = storage.get(
        "surveys",
        survey_id,
    )

    if not rec:
        raise HTTPException(
            404,
            "Survey not found",
        )

    return rec


# ============================================================
# DELETE SURVEY
# ============================================================

@router.delete(
    "/surveys/{survey_id}"
)
async def delete_survey(
    survey_id: str,
):

    rec = storage.get(
        "surveys",
        survey_id,
    )

    if not rec:
        raise HTTPException(
            404,
            "Survey not found",
        )

    # --------------------------------------------------------
    # Delete current image
    # --------------------------------------------------------

    current_path = rec.get(
        "current_image_path",
        rec.get(
            "image_path"
        ),
    )

    if (
        current_path
        and os.path.exists(
            current_path
        )
    ):
        os.remove(
            current_path
        )

    # --------------------------------------------------------
    # Delete previous image
    # --------------------------------------------------------

    previous_path = rec.get(
        "previous_image_path"
    )

    if (
        previous_path
        and os.path.exists(
            previous_path
        )
    ):
        os.remove(
            previous_path
        )

    # --------------------------------------------------------
    # Delete database record
    # --------------------------------------------------------

    storage.delete(
        "surveys",
        survey_id,
    )

    return {
        "deleted":
            survey_id
    }