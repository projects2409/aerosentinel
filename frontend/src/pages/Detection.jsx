import {
  useEffect,
  useRef,
  useState,
} from "react";

import { api } from "../api";


export default function Detection() {

  // ============================================================
  // EXISTING SURVEY STATE
  // ============================================================

  const [surveys, setSurveys] = useState([]);
  const [mode, setMode] = useState(null);
  const [selected, setSelected] = useState([]);
  const [compareResult, setCompareResult] =
    useState(null);

  const [busy, setBusy] = useState(null);
  const [error, setError] = useState(null);


  // ============================================================
  // DRONE / WEBCAM STATE
  // ============================================================

  const videoRef = useRef(null);

  // Hidden canvas used to capture frames
  const canvasRef = useRef(null);

  // Visible canvas used to draw YOLO boxes
  const overlayCanvasRef =
    useRef(null);

  const streamRef = useRef(null);
  const timerRef = useRef(null);

  const [droneRunning, setDroneRunning] =
    useState(false);

  const [droneStatus, setDroneStatus] =
    useState(null);

  const [droneModel, setDroneModel] =
    useState(null);

  const [droneDetections, setDroneDetections] =
    useState([]);

  const [droneMessage, setDroneMessage] =
    useState(
      "Drone monitoring is ready."
    );

  const [lastReport, setLastReport] =
    useState(null);

  const [droneBusy, setDroneBusy] =
    useState(false);


  // ============================================================
  // INITIAL LOAD
  // ============================================================

  useEffect(() => {

    loadSurveys();

    api.detectionMode()
      .then(setMode)
      .catch(() => {});

    api.droneStatus()
      .then(setDroneStatus)
      .catch(() => {});

    api.droneModel()
      .then(setDroneModel)
      .catch(() => {});


    return () => {
      stopDrone();
    };

  }, []);


  // ============================================================
  // LOAD SURVEYS
  // ============================================================

  const loadSurveys = () => {

    api.listSurveys()
      .then(setSurveys)
      .catch((e) =>
        setError(e.message)
      );

  };


  // ============================================================
  // EXISTING SURVEY DETECTION
  // ============================================================

  const runDetection = async (
    surveyId
  ) => {

    setBusy(surveyId);
    setError(null);

    try {

      await api.runDetection(
        surveyId
      );

      const fresh =
        await api.listSurveys();

      setSurveys(fresh);

    } catch (e) {

      setError(e.message);

    } finally {

      setBusy(null);

    }

  };


  // ============================================================
  // SURVEY SELECTION
  // ============================================================

  const toggleSelected = (
    id
  ) => {

    setSelected((prev) =>
      prev.includes(id)
        ? prev.filter(
            (x) => x !== id
          )
        : [...prev, id]
    );

  };


  // ============================================================
  // COMPARE SURVEYS
  // ============================================================

  const runCompare = async () => {

    setError(null);

    try {

      const res =
        await api.compareSurveys(
          selected
        );

      setCompareResult(res);

    } catch (e) {

      setError(e.message);

    }

  };


  // ============================================================
  // DRAW YOLO BOXES
  // ============================================================

  const drawDetections = (detections = []) => {
    const canvas = overlayCanvasRef.current;
    const video = videoRef.current;

    if (!canvas || !video) return;

    const rect = video.getBoundingClientRect();
    const displayWidth = rect.width;
    const displayHeight = rect.height;
    const sourceWidth = video.videoWidth;
    const sourceHeight = video.videoHeight;

    if (!displayWidth || !displayHeight || !sourceWidth || !sourceHeight) {
      return;
    }

    canvas.width = Math.round(displayWidth);
    canvas.height = Math.round(displayHeight);

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const scaleX = displayWidth / sourceWidth;
    const scaleY = displayHeight / sourceHeight;

    console.log("DRAWING DETECTIONS:", detections.length, {
      sourceWidth,
      sourceHeight,
      displayWidth,
      displayHeight,
    });

    detections.forEach((detection, index) => {
      const box = detection?.bbox;

      if (!box) {
        console.warn("Detection has no bbox:", detection);
        return;
      }

      const x1 = Number(box.x1);
      const y1 = Number(box.y1);
      const x2 = Number(box.x2);
      const y2 = Number(box.y2);

      if (
        !Number.isFinite(x1) ||
        !Number.isFinite(y1) ||
        !Number.isFinite(x2) ||
        !Number.isFinite(y2)
      ) {
        console.warn("Invalid bbox:", box);
        return;
      }

      const left = x1 * scaleX;
      const top = y1 * scaleY;
      const width = (x2 - x1) * scaleX;
      const height = (y2 - y1) * scaleY;

      console.log(`BOX ${index}:`, {
        x1, y1, x2, y2, left, top, width, height,
      });

      ctx.strokeStyle = "#00ff66";
      ctx.lineWidth = 4;
      ctx.strokeRect(left, top, width, height);

      const confidence = Number(detection.confidence);
      const confidenceText = Number.isFinite(confidence)
        ? `${(confidence * 100).toFixed(0)}%`
        : "";

      const label = `${detection.class_name || "PERSON"} ${confidenceText}`;

      ctx.font = "bold 16px Arial";
      const textWidth = ctx.measureText(label).width;
      const labelHeight = 26;

      const labelX = Math.max(
        0,
        Math.min(left, canvas.width - textWidth - 12)
      );

      const labelY = Math.max(labelHeight, top);

      ctx.fillStyle = "#00ff66";
      ctx.fillRect(
        labelX,
        labelY - labelHeight,
        textWidth + 12,
        labelHeight
      );

      ctx.fillStyle = "#000000";
      ctx.fillText(label, labelX + 6, labelY - 7);
    });
  };

  // ============================================================
  // START DRONE CAMERA
  // ============================================================

  const startDrone = async () => {

    setError(null);

    try {

      const stream =
        await navigator.mediaDevices.getUserMedia(
          {
            video: {
              width: {
                ideal: 1280,
              },

              height: {
                ideal: 720,
              },

              facingMode:
                "user",
            },

            audio: false,
          }
        );


      streamRef.current =
        stream;


      if (
        videoRef.current
      ) {

        videoRef.current.srcObject =
          stream;

        await videoRef.current.play();

      }


      setDroneRunning(
        true
      );


      setDroneMessage(
        "Camera active. Establishing baseline..."
      );


      setLastReport(null);

      setDroneDetections(
        []
      );


      // Clear old boxes
      if (
        overlayCanvasRef.current
      ) {

        const ctx =
          overlayCanvasRef.current.getContext(
            "2d"
          );

        ctx.clearRect(
          0,
          0,
          overlayCanvasRef.current.width,
          overlayCanvasRef.current.height
        );

      }


      // Give camera time to initialize
      setTimeout(() => {

        startFrameLoop();

      }, 1000);


    } catch (e) {

      console.error(
        "Camera error:",
        e
      );

      setError(
        "Could not access your webcam. Please allow camera permission in the browser."
      );

    }

  };


  // ============================================================
  // STOP DRONE CAMERA
  // ============================================================

  const stopDrone = () => {

    if (
      timerRef.current
    ) {

      clearInterval(
        timerRef.current
      );

      timerRef.current =
        null;

    }


    if (
      streamRef.current
    ) {

      streamRef.current
        .getTracks()
        .forEach(
          (track) =>
            track.stop()
        );

      streamRef.current =
        null;

    }


    if (
      videoRef.current
    ) {

      videoRef.current.srcObject =
        null;

    }


    // Clear visible boxes
    if (
      overlayCanvasRef.current
    ) {

      const canvas =
        overlayCanvasRef.current;

      const ctx =
        canvas.getContext(
          "2d"
        );

      ctx.clearRect(
        0,
        0,
        canvas.width,
        canvas.height
      );

    }


    setDroneRunning(
      false
    );

    setDroneDetections(
      []
    );

    setDroneMessage(
      "Drone monitoring stopped."
    );

  };


  // ============================================================
  // PROCESS WEBCAM FRAME
  // ============================================================

  const processFrame = async () => {

    if (
      !videoRef.current ||
      !canvasRef.current ||
      droneBusy
    ) {
      return;
    }


    if (
      videoRef.current.readyState <
      2
    ) {
      return;
    }


    setDroneBusy(
      true
    );


    try {

      const video =
        videoRef.current;

      const canvas =
        canvasRef.current;


      const width =
        video.videoWidth ||
        1280;

      const height =
        video.videoHeight ||
        720;


      // Hidden canvas used to create
      // the image sent to YOLO.

      canvas.width =
        width;

      canvas.height =
        height;


      const ctx =
        canvas.getContext(
          "2d"
        );


      ctx.drawImage(
        video,
        0,
        0,
        width,
        height
      );


      const blob =
        await new Promise(
          (resolve) =>
            canvas.toBlob(
              resolve,
              "image/jpeg",
              0.8
            )
        );


      if (!blob) {
        return;
      }


      // ========================================================
      // SEND FRAME TO CDAC YOLO
      // ========================================================

      const result =
        await api.detectDroneFrame(
          blob
        );


      console.log(
        "CDAC YOLO result:",
        result
      );


      const detections =
        result.detections ||
        [];


      setDroneDetections(
        detections
      );


      // ========================================================
      // DRAW BOXES
      // ========================================================

      drawDetections(
        detections
      );


      // ========================================================
      // BASELINE
      // ========================================================

      if (
        result.status ===
        "baseline_created"
      ) {

        setDroneMessage(
          detections.length >
          0
            ? "AI scan active. Baseline created. Monitoring for changes..."
            : "Baseline created. AI scanning for changes..."
        );

        return;
      }


      // ========================================================
      // DETECTION EXISTS BUT NO CHANGE
      // ========================================================

      if (
        detections.length >
          0 &&
        !result.change_detected
      ) {

        setDroneMessage(
          "AI detection active. Monitoring the area for changes..."
        );

        return;
      }


      // ========================================================
      // NO DETECTION / NO CHANGE
      // ========================================================

      if (
        !result.change_detected
      ) {

        setDroneMessage(
          "AI scanning... no new change detected."
        );

        return;
      }


      // ========================================================
      // CHANGE DETECTED
      // ========================================================

      if (
        result.change_detected
      ) {

        if (
          result.report_created
        ) {

          setDroneMessage(
            "🚨 CHANGE DETECTED — REPORT CREATED"
          );


          setLastReport(
            result
          );

        } else {

          setDroneMessage(
            "🚨 Change detected — processing report..."
          );

        }

      }


    } catch (e) {

      console.error(
        "Drone frame error:",
        e
      );


      setDroneMessage(
        `Drone processing error: ${e.message}`
      );


    } finally {

      setDroneBusy(
        false
      );

    }

  };


  // ============================================================
  // START REPEATED FRAME PROCESSING
  // ============================================================

  const startFrameLoop = () => {

    if (
      timerRef.current
    ) {

      clearInterval(
        timerRef.current
      );

    }


    // Process approximately
    // once every 1.5 seconds.

    timerRef.current =
      setInterval(
        processFrame,
        1500
      );


    // Process immediately
    processFrame();

  };


  // ============================================================
  // UI
  // ============================================================

  return (
    <>
      <h2>
        Detection & Drone Monitoring
      </h2>


      {/* ======================================================
          SURVEY DETECTION MODE
      ======================================================= */}

      {mode && (
        <div className="card">

          Current survey detection mode:

          <span
            className={`badge ${
              mode.mock_mode
                ? "mock"
                : "real"
            }`}
            style={{
              marginLeft: 8,
            }}
          >
            {mode.mock_mode
              ? "MOCK"
              : "REAL"}
          </span>


          {!mode.mock_mode && (
            <span
              style={{
                marginLeft: 8,
                color:
                  "var(--muted)",
              }}
            >
              CDAC YOLO weights loaded.
            </span>
          )}


          {mode.mock_mode && (
            <span
              style={{
                marginLeft: 8,
                color:
                  "var(--muted)",
              }}
            >
              Put best.pt inside
              backend/weights/
              to use the real CDAC model.
            </span>
          )}

        </div>
      )}


      {/* ======================================================
          SURVEY IMAGE DETECTION
      ======================================================= */}

      <div className="card">

        <h3>
          Survey Image Detection
        </h3>


        <p
          style={{
            color:
              "var(--muted)",
            fontSize: 13,
          }}
        >
          Upload multiple survey images,
          run the CDAC YOLO model on each,
          and compare the previous survey
          data to identify changes.
        </p>


        <table>

          <thead>

            <tr>

              <th>
                Select
              </th>

              <th>
                Label
              </th>

              <th>
                Filename
              </th>

              <th>
                Detection
              </th>

              <th>
              </th>

            </tr>

          </thead>


          <tbody>

            {surveys.map(
              (s) => (

                <tr
                  key={s.id}
                >

                  <td>

                    <input
                      type="checkbox"
                      checked={selected.includes(
                        s.id
                      )}
                      onChange={() =>
                        toggleSelected(
                          s.id
                        )
                      }
                    />

                  </td>


                  <td>
                    {s.label}
                  </td>


                  <td>
                    {s.filename}
                  </td>


                  <td>
                    {s.detections_run
                      ? "Yes"
                      : "No"}
                  </td>


                  <td>

                    <button
                      className="btn secondary"
                      disabled={
                        busy ===
                        s.id
                      }
                      onClick={() =>
                        runDetection(
                          s.id
                        )
                      }
                    >

                      {busy ===
                      s.id
                        ? "Running..."
                        : "Run detection"}

                    </button>

                  </td>

                </tr>

              )
            )}

          </tbody>

        </table>

      </div>


      {/* ======================================================
          COMPARE SURVEY HISTORY
      ======================================================= */}

      <div className="card">

        <h3>
          Compare Survey History
        </h3>


        <p
          style={{
            color:
              "var(--muted)",
            fontSize: 13,
          }}
        >
          Select two or more processed
          surveys. The system uses the
          previous survey data as the
          reference and identifies
          NEW, REMOVED, PERSISTENT or
          CHANGED detections.
        </p>


        <button
          className="btn"
          disabled={
            selected.length <
            2
          }
          onClick={
            runCompare
          }
        >
          Compare{" "}
          {selected.length} surveys
        </button>


        {compareResult && (
          <p
            style={{
              marginTop: 10,
            }}
          >
            Found{" "}
            <strong>
              {
                compareResult.change_count
              }
            </strong>{" "}
            change records.
          </p>
        )}

      </div>


      {/* ======================================================
          DRONE MONITORING
      ======================================================= */}

      <div
        className="card"
        style={{
          marginTop: 25,
          border:
            "1px solid rgba(255,255,255,0.12)",
        }}
      >

        <div
          style={{
            display:
              "flex",
            justifyContent:
              "space-between",
            alignItems:
              "center",
            gap: 10,
          }}
        >

          <div>

            <h3>
              🚁 Drone Monitoring
            </h3>


            <p
              style={{
                color:
                  "var(--muted)",
                fontSize: 13,
                marginBottom: 0,
              }}
            >
              Laptop webcam prototype
              using the CDAC-trained YOLO
              model.
            </p>

          </div>


          <span
            className={`badge ${
              droneRunning
                ? "real"
                : "mock"
            }`}
          >
            {droneRunning
              ? "● LIVE"
              : "OFFLINE"}
          </span>

        </div>


        <div
          className="grid"
          style={{
            marginTop: 20,
          }}
        >


          {/* ==================================================
              LARGE LIVE VIDEO
          ================================================== */}

          <div>

            <div
              style={{
                position:
                  "relative",

                background:
                  "#050505",

                borderRadius: 10,

                overflow:
                  "hidden",

                width:
                  "100%",

                minHeight:
                  500,
              }}
            >

              {/* ==============================================
                  LIVE VIDEO
              =============================================== */}

              <video
                ref={
                  videoRef
                }

                muted

                playsInline

                autoPlay

                style={{
                  width:
                    "100%",

                  height:
                    "100%",

                  minHeight:
                    500,

                  display:
                    "block",

                  objectFit:
                    "fill",

                  background:
                    "#050505",
                }}
              />


              {/* ==============================================
                  YOLO BOUNDING BOX OVERLAY
              =============================================== */}

              <canvas
                ref={
                  overlayCanvasRef
                }

                style={{
                  position:
                    "absolute",

                  top: 0,

                  left: 0,

                  width:
                    "100%",

                  height:
                    "100%",

                  pointerEvents:
                    "none",

                  zIndex: 10,
                }}
              />


              {/* ==============================================
                  LIVE INDICATOR
              =============================================== */}

              {droneRunning && (
                <div
                  style={{
                    position:
                      "absolute",

                    top: 15,

                    left: 15,

                    background:
                      "rgba(0,0,0,0.75)",

                    color:
                      "#ffffff",

                    padding:
                      "8px 12px",

                    borderRadius:
                      6,

                    fontWeight:
                      700,

                    fontSize:
                      14,

                    zIndex:
                      5,
                  }}
                >
                  ● LIVE AI SCAN
                </div>
              )}


              {/* ==============================================
                  OFFLINE MESSAGE
              =============================================== */}

              {!droneRunning && (
                <div
                  style={{
                    position:
                      "absolute",

                    inset: 0,

                    display:
                      "flex",

                    alignItems:
                      "center",

                    justifyContent:
                      "center",

                    color:
                      "var(--muted)",

                    pointerEvents:
                      "none",
                  }}
                >
                  🚁 Drone camera
                  offline
                </div>
              )}

            </div>


            {/* Hidden frame capture canvas */}

            <canvas
              ref={
                canvasRef
              }

              style={{
                display:
                  "none",
              }}
            />


            {/* ==================================================
                CAMERA CONTROLS
            ================================================== */}

            <div
              style={{
                marginTop:
                  12,

                display:
                  "flex",

                gap: 10,
              }}
            >

              {!droneRunning ? (

                <button
                  className="btn"
                  onClick={
                    startDrone
                  }
                >
                  🚁 Start Drone Monitoring
                </button>

              ) : (

                <button
                  className="btn secondary"
                  onClick={
                    stopDrone
                  }
                >
                  Stop Monitoring
                </button>

              )}

            </div>

          </div>


          {/* ==================================================
              DETECTION STATUS
          ================================================== */}

          <div>

            <div
              className="card"
              style={{
                margin: 0,
              }}
            >

              <h3>
                AI Monitoring Status
              </h3>


              <p>
                Status:{" "}
                <strong>
                  {droneRunning
                    ? "Monitoring"
                    : "Waiting"}
                </strong>
              </p>


              <p>
                Source:{" "}
                <strong>
                  🚁 Drone Camera
                </strong>
              </p>


              <p>
                Model:{" "}
                <strong>
                  {droneModel?.mock_mode
                    ? "MOCK"
                    : "CDAC YOLO"}
                </strong>
              </p>


              <p>
                Detections:{" "}
                <strong>
                  {droneDetections.length}
                </strong>
              </p>


              <p
                style={{
                  color:
                    "var(--muted)",

                  fontSize:
                    13,
                }}
              >
                {droneMessage}
              </p>


              {/* ==================================================
                  DETECTIONS
              ================================================== */}

              {droneDetections.length >
                0 && (

                <div>

                  <h4>
                    AI detections
                  </h4>


                  {droneDetections.map(
                    (
                      detection,
                      index
                    ) => (

                      <div
                        key={
                          index
                        }
                        style={{
                          padding:
                            "8px 0",

                          borderBottom:
                            "1px solid rgba(255,255,255,0.08)",
                        }}
                      >

                        <strong>
                          AI Change
                        </strong>


                        <br />


                        Confidence:{" "}

                        {(
                          detection.confidence *
                          100
                        ).toFixed(1)}

                        %

                      </div>

                    )
                  )}

                </div>

              )}

            </div>


            {/* ==================================================
                AUTOMATIC REPORT
            ================================================== */}

            {lastReport && (

              <div
                className="card"
                style={{
                  marginTop:
                    15,

                  border:
                    "1px solid rgba(255,70,70,0.45)",
                }}
              >

                <h3>
                  🚨 Change Detected
                </h3>


                <p>

                  <strong>
                    Source:
                  </strong>{" "}

                  🚁 Drone / CDAC YOLO

                </p>


                <p>

                  <strong>
                    Detection:
                  </strong>{" "}

                  AI Change

                </p>


                <p>

                  <strong>
                    Confidence:
                  </strong>{" "}

                  {(
                    lastReport.confidence *
                    100
                  ).toFixed(1)}

                  %

                </p>


                <p>

                  <strong>
                    Priority:
                  </strong>{" "}

                  {lastReport.priority_score}
                  /100

                </p>


                <p>

                  <strong>
                    Location:
                  </strong>{" "}

                  {lastReport.lat?.toFixed(
                    6
                  )}

                  ,{" "}

                  {lastReport.lon?.toFixed(
                    6
                  )}

                </p>


                <p
                  style={{
                    color:
                      "var(--success)",
                  }}
                >
                  ✓ Report automatically
                  generated
                </p>


                <p
                  style={{
                    color:
                      "var(--success)",
                  }}
                >
                  ✓ Red map marker created
                </p>

              </div>

            )}

          </div>

        </div>

      </div>


      {/* ======================================================
          ERROR
      ======================================================= */}

      {error && (

        <p
          style={{
            color:
              "var(--danger)",
          }}
        >
          {error}
        </p>

      )}

    </>
  );
}