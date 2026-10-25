const BASE = "/api";


// ============================================================
// COMMON RESPONSE HANDLER
// ============================================================

async function handle(res) {
  if (!res.ok) {
    let detail = res.statusText;

    try {
      const body = await res.json();

      detail =
        body.detail ||
        body.message ||
        detail;
    } catch (_) {
      // Response was not JSON.
    }

    throw new Error(detail);
  }

  return res.json();
}


// ============================================================
// API
// ============================================================

export const api = {

  // ==========================================================
  // SURVEY UPLOAD
  // ==========================================================

  /*
   * Upload a survey.
   *
   * currentFile  = REQUIRED
   * previousFile = OPTIONAL
   *
   * This allows:
   *
   * 1 image:
   *   Current image only
   *
   * OR
   *
   * 2 images:
   *   Previous image
   *   +
   *   Current image
   */

  uploadSurvey: (
    currentFile,
    label,
    lat,
    lon,
    previousFile = null
  ) => {
    const fd = new FormData();

    // --------------------------------------------------------
    // Current / With Change image
    // REQUIRED
    // --------------------------------------------------------

    fd.append(
      "file",
      currentFile
    );

    // --------------------------------------------------------
    // Survey information
    // --------------------------------------------------------

    fd.append(
      "label",
      label
    );

    if (
      lat !== undefined &&
      lat !== null &&
      lat !== ""
    ) {
      fd.append(
        "lat",
        lat
      );
    }

    if (
      lon !== undefined &&
      lon !== null &&
      lon !== ""
    ) {
      fd.append(
        "lon",
        lon
      );
    }

    // --------------------------------------------------------
    // Previous / Without Change image
    // OPTIONAL
    // --------------------------------------------------------

    if (previousFile) {
      fd.append(
        "previous_file",
        previousFile
      );
    }

    return fetch(
      `${BASE}/upload/survey`,
      {
        method: "POST",
        body: fd,
      }
    ).then(handle);
  },


  // ==========================================================
  // LIST SURVEYS
  // ==========================================================

  listSurveys: () =>
    fetch(
      `${BASE}/upload/surveys`
    ).then(handle),


  // ==========================================================
  // GET ONE SURVEY
  // ==========================================================

  getSurvey: (
    surveyId
  ) =>
    fetch(
      `${BASE}/upload/surveys/${surveyId}`
    ).then(handle),


  // ==========================================================
  // DELETE SURVEY
  // ==========================================================

  deleteSurvey: (
    id
  ) =>
    fetch(
      `${BASE}/upload/surveys/${id}`,
      {
        method: "DELETE",
      }
    ).then(handle),


  // ==========================================================
  // YOLO DETECTION
  // ==========================================================

  detectionMode: () =>
    fetch(
      `${BASE}/detection/mode`
    ).then(handle),


  runDetection: (
    surveyId
  ) =>
    fetch(
      `${BASE}/detection/run/${surveyId}`,
      {
        method: "POST",
      }
    ).then(handle),


  getDetections: (
    surveyId
  ) =>
    fetch(
      `${BASE}/detection/survey/${surveyId}`
    ).then(handle),


  // ==========================================================
  // TEMPORAL COMPARISON
  // ==========================================================

  compareSurveys: (
    surveyIds
  ) =>
    fetch(
      `${BASE}/temporal/compare`,
      {
        method: "POST",

        headers: {
          "Content-Type":
            "application/json",
        },

        body: JSON.stringify({
          survey_ids:
            surveyIds,
        }),
      }
    ).then(handle),


  listChanges: () =>
    fetch(
      `${BASE}/temporal/changes`
    ).then(handle),


  getChange: (
    id
  ) =>
    fetch(
      `${BASE}/temporal/changes/${id}`
    ).then(handle),


  // ==========================================================
  // DRONE
  // ==========================================================

  droneModel: () =>
    fetch(
      `${BASE}/drone/model`
    ).then(handle),


  droneStatus: () =>
    fetch(
      `${BASE}/drone/status`
    ).then(handle),


  startDrone: () =>
    fetch(
      `${BASE}/drone/start`,
      {
        method: "POST",
      }
    ).then(handle),


  stopDrone: () =>
    fetch(
      `${BASE}/drone/stop`,
      {
        method: "POST",
      }
    ).then(handle),


  /*
   * Send one webcam frame to the drone
   * detection endpoint.
   *
   * The backend runs the CDAC YOLO model
   * and returns detections + bounding boxes.
   */

  detectDroneFrame: (
    blob
  ) => {
    const fd = new FormData();

    fd.append(
      "file",
      blob,
      "drone_frame.jpg"
    );

    return fetch(
      `${BASE}/drone/detect`,
      {
        method: "POST",
        body: fd,
      }
    ).then(handle);
  },


  // ==========================================================
  // GEOSPATIAL
  // ==========================================================

  getBoundaries: () =>
    fetch(
      `${BASE}/geospatial/boundaries`
    ).then(handle),


  analyzeChange: (
    changeId
  ) =>
    fetch(
      `${BASE}/geospatial/analyze/${changeId}`,
      {
        method: "POST",
      }
    ).then(handle),


  // ==========================================================
  // PRIORITY
  // ==========================================================

  scoreChange: (
    changeId
  ) =>
    fetch(
      `${BASE}/priority/score/${changeId}`,
      {
        method: "POST",
      }
    ).then(handle),


  rankedCases: () =>
    fetch(
      `${BASE}/priority/ranked`
    ).then(handle),


  // ==========================================================
  // REPORTS
  // ==========================================================

  generateReport: (
    changeId
  ) =>
    fetch(
      `${BASE}/reports/generate/${changeId}`,
      {
        method: "POST",
      }
    ).then(handle),


  listReports: () =>
    fetch(
      `${BASE}/reports/list`
    ).then(handle),


  reportDownloadUrl: (
    reportId
  ) =>
    `${BASE}/reports/download/${reportId}`,
};