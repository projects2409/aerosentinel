import {
  useEffect,
  useState,
} from "react";

import {
  useParams,
} from "react-router-dom";

import { api } from "../api";

import MapView from "../components/MapView.jsx";


export default function CaseDetail() {

  const { id } =
    useParams();


  const [
    change,
    setChange,
  ] = useState(null);


  const [
    error,
    setError,
  ] = useState(null);


  const [
    reportUrl,
    setReportUrl,
  ] = useState(null);


  const [
    busy,
    setBusy,
  ] = useState(false);


  const load = () => {

    api
      .getChange(id)
      .then(setChange)
      .catch((e) =>
        setError(
          e.message
        )
      );

  };


  useEffect(() => {
    load();
  }, [id]);


  const generate = async () => {

    setBusy(true);
    setError(null);

    try {

      const res =
        await api.generateReport(
          id
        );

      setReportUrl(
        api.reportDownloadUrl(
          res.report_id
        )
      );

    } catch (e) {

      setError(
        e.message
      );

    } finally {

      setBusy(false);

    }
  };


  if (!change) {

    return (
      <p>
        Loading...
      </p>
    );

  }


  const isDrone =
    change.source ===
    "drone";


  return (

    <>

      <h2>

        {isDrone
          ? "🚁 Drone Case"
          : "👤 User Case"}

        {" — "}

        {change.class_name}

        {" "}

        <span
          className={`badge ${change.change_type}`}
        >
          {change.change_type}
        </span>

      </h2>


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


      <div className="grid">


        <div className="card">

          <h3>
            Detection Summary
          </h3>


          <p>
            <strong>
              Source:
            </strong>{" "}

            {isDrone
              ? "🚁 Drone / CDAC YOLO"
              : "👤 User Report"}

          </p>


          <p>
            <strong>
              Model:
            </strong>{" "}

            {change.model ??
              "N/A"}

          </p>


          <p>
            <strong>
              Change:
            </strong>{" "}

            {change.change_type}

          </p>


          <p>
            <strong>
              Confidence:
            </strong>{" "}

            {change.avg_confidence !=
            null
              ? (
                  change.avg_confidence *
                  100
                ).toFixed(1) +
                "%"
              : "—"}

          </p>


          <p>
            <strong>
              Priority:
            </strong>{" "}

            {change.priority_score ??
              "Not scored"}

          </p>


          <p>
            <strong>
              Zone:
            </strong>{" "}

            {change.zone_name ??
              "Not analyzed"}

          </p>

        </div>


        <div className="card">

          <h3>
            Priority Reasoning
          </h3>


          {(!change.priority_reasons ||
            change.priority_reasons.length ===
              0) && (

            <p>
              No priority reasoning
              available.
            </p>

          )}


          <ul className="reasons">

            {change.priority_reasons?.map(
              (reason, index) => (

                <li
                  key={index}
                >
                  {reason}
                </li>

              )
            )}

          </ul>

        </div>

      </div>


      {/* Evidence */}

      {isDrone &&
        change.evidence_path && (

          <div className="card">

            <h3>
              🚁 Drone Evidence
            </h3>

            <p
              style={{
                color:
                  "var(--muted)",
              }}
            >
              Image captured automatically
              when the CDAC YOLO model
              detected a change.
            </p>

            <img
              src={
                `/media/${change.evidence_filename}`
              }
              alt="Drone detection evidence"
              style={{
                width: "100%",
                maxWidth: 900,
                borderRadius: 10,
              }}
            />

          </div>

        )}


      {/* Map */}

      {change.lat != null &&
        change.lon != null && (

          <div className="card">

            <h3>
              Location
            </h3>

            <MapView
              cases={[
                change,
              ]}
              center={[
                change.lat,
                change.lon,
              ]}
              height={350}
            />

          </div>

        )}


      {/* Report */}

      <div className="card">

        <h3>
          Evidence Report
        </h3>


        <button
          className="btn"
          disabled={
            change.priority_score ==
              null ||
            busy
          }
          onClick={generate}
        >

          {busy
            ? "Generating..."
            : "Generate PDF report"}

        </button>


        {change.priority_score ==
          null && (

          <p
            style={{
              color:
                "var(--muted)",
              fontSize: 13,
            }}
          >
            This case needs a priority
            score before a PDF can be
            generated.
          </p>

        )}


        {reportUrl && (

          <p
            style={{
              marginTop: 10,
            }}
          >

            <a
              className="btn secondary"
              href={reportUrl}
              target="_blank"
              rel="noreferrer"
            >
              Download report
            </a>

          </p>

        )}

      </div>

    </>

  );
}