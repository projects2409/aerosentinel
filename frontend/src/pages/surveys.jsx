import { useEffect, useState } from "react";
import { api } from "../api";

export default function Surveys() {
  const [surveys, setSurveys] = useState([]);

  // Current / changed image
  const [currentFile, setCurrentFile] =
    useState(null);

  // Previous / without-change image
  // OPTIONAL
  const [previousFile, setPreviousFile] =
    useState(null);

  const [label, setLabel] =
    useState("T1");

  const [lat, setLat] =
    useState("29.863");

  const [lon, setLon] =
    useState("77.875");

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState(null);

  const load = () =>
    api
      .listSurveys()
      .then(setSurveys)
      .catch((e) =>
        setError(e.message)
      );

  useEffect(() => {
    load();
  }, []);

  const handleUpload = async (e) => {
    e.preventDefault();

    // Current image is required
    if (!currentFile) {
      setError(
        "Please select the current / changed image."
      );
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await api.uploadSurvey(
        currentFile,
        label,
        lat,
        lon,
        previousFile
      );

      // Reset files after upload
      setCurrentFile(null);
      setPreviousFile(null);

      // Reset the actual file inputs
      const currentInput =
        document.getElementById(
          "current-survey-image"
        );

      const previousInput =
        document.getElementById(
          "previous-survey-image"
        );

      if (currentInput) {
        currentInput.value = "";
      }

      if (previousInput) {
        previousInput.value = "";
      }

      await load();

    } catch (err) {
      setError(
        err.message
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <h2>Surveys</h2>

      <div className="card">
        <h3>
          Upload survey imagery
        </h3>

        <p
          style={{
            color:
              "var(--muted)",
            fontSize: 13,
            marginBottom: 15,
          }}
        >
          Upload the current image
          containing the change. A
          previous / without-change
          image can also be uploaded
          for comparison, but it is
          optional.
        </p>

        <form
          onSubmit={
            handleUpload
          }
        >
          <div className="grid">

            {/* ============================================
                SURVEY LABEL
            ============================================= */}

            <div>
              <label>
                Survey label
                (T1 / T2 / T3...)
              </label>

              <input
                value={label}
                onChange={(e) =>
                  setLabel(
                    e.target.value
                  )
                }
              />
            </div>

            {/* ============================================
                LATITUDE
            ============================================= */}

            <div>
              <label>
                Latitude
                (sample georeferencing
                anchor)
              </label>

              <input
                value={lat}
                onChange={(e) =>
                  setLat(
                    e.target.value
                  )
                }
              />
            </div>

            {/* ============================================
                LONGITUDE
            ============================================= */}

            <div>
              <label>
                Longitude
              </label>

              <input
                value={lon}
                onChange={(e) =>
                  setLon(
                    e.target.value
                  )
                }
              />
            </div>

            {/* ============================================
                CURRENT / CHANGED IMAGE
            ============================================= */}

            <div>
              <label>
                Current / With Change
                image *
              </label>

              <input
                id="current-survey-image"
                type="file"
                accept="image/*"
                onChange={(e) =>
                  setCurrentFile(
                    e.target.files?.[0] ||
                    null
                  )
                }
              />

              <small
                style={{
                  display:
                    "block",
                  marginTop: 5,
                  color:
                    "var(--muted)",
                }}
              >
                Required
              </small>

              {currentFile && (
                <small
                  style={{
                    display:
                      "block",
                    marginTop: 5,
                  }}
                >
                  ✓{" "}
                  {
                    currentFile.name
                  }
                </small>
              )}
            </div>

            {/* ============================================
                PREVIOUS / WITHOUT CHANGE IMAGE
            ============================================= */}

            <div>
              <label>
                Previous / Without
                Change image
              </label>

              <input
                id="previous-survey-image"
                type="file"
                accept="image/*"
                onChange={(e) =>
                  setPreviousFile(
                    e.target.files?.[0] ||
                    null
                  )
                }
              />

              <small
                style={{
                  display:
                    "block",
                  marginTop: 5,
                  color:
                    "var(--muted)",
                }}
              >
                Optional — upload
                this only if you
                have the previous
                image.
              </small>

              {previousFile && (
                <small
                  style={{
                    display:
                      "block",
                    marginTop: 5,
                  }}
                >
                  ✓{" "}
                  {
                    previousFile.name
                  }
                </small>
              )}
            </div>
          </div>

          {/* ============================================
              UPLOAD BUTTON
          ============================================= */}

          <div
            style={{
              marginTop: 12,
            }}
          >
            <button
              className="btn"
              disabled={
                !currentFile ||
                loading
              }
              type="submit"
            >
              {loading
                ? "Uploading..."
                : previousFile
                ? "Upload & Compare"
                : "Upload survey"}
            </button>
          </div>
        </form>

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
      </div>

      {/* ================================================
          UPLOADED SURVEYS
      ================================================= */}

      <div className="card">
        <h3>
          Uploaded surveys
        </h3>

        {surveys.length === 0 && (
          <p>
            No surveys uploaded
            yet.
          </p>
        )}

        {surveys.length > 0 && (
          <table>
            <thead>
              <tr>
                <th>
                  Label
                </th>

                <th>
                  Filename
                </th>

                <th>
                  Uploaded
                </th>

                <th>
                  Detections run
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
                      {
                        s.label
                      }
                    </td>

                    <td>
                      {
                        s.filename
                      }
                    </td>

                    <td>
                      {new Date(
                        s.uploaded_at
                      ).toLocaleString()}
                    </td>

                    <td>
                      {s.detections_run
                        ? "Yes"
                        : "No"}
                    </td>

                    <td>
                      <button
                        className="btn secondary"
                        onClick={async () => {
                          await api.deleteSurvey(
                            s.id
                          );

                          load();
                        }}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                )
              )}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}