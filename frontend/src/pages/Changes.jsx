import {
  useEffect,
  useState,
} from "react";

import {
  useNavigate,
} from "react-router-dom";

import { api } from "../api";


export default function Changes() {

  const [
    changes,
    setChanges,
  ] = useState([]);

  const [
    busyId,
    setBusyId,
  ] = useState(null);

  const [
    error,
    setError,
  ] = useState(null);

  const navigate =
    useNavigate();


  const load = () => {

    api
      .listChanges()
      .then(setChanges)
      .catch((e) =>
        setError(e.message)
      );

  };


  useEffect(() => {
    load();
  }, []);


  const runGeo = async (
    id
  ) => {

    setBusyId(id);
    setError(null);

    try {

      await api.analyzeChange(
        id
      );

      load();

    } catch (e) {

      setError(
        e.message
      );

    } finally {

      setBusyId(null);

    }
  };


  const runScore = async (
    id
  ) => {

    setBusyId(id);
    setError(null);

    try {

      await api.scoreChange(
        id
      );

      load();

    } catch (e) {

      setError(
        e.message
      );

    } finally {

      setBusyId(null);

    }
  };


  return (

    <>

      <h2>
        Changes
      </h2>


      <div className="card">

        <p
          style={{
            color:
              "var(--muted)",
            fontSize: 13,
          }}
        >
          This page contains changes
          detected from uploaded surveys
          and automatically detected by
          the drone monitoring system.
        </p>


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


        {changes.length === 0 && (
          <p>
            No changes yet.
          </p>
        )}


        {changes.length > 0 && (

          <table>

            <thead>

              <tr>

                <th>
                  Source
                </th>

                <th>
                  Class
                </th>

                <th>
                  Type
                </th>

                <th>
                  Confidence
                </th>

                <th>
                  Zone
                </th>

                <th>
                  Score
                </th>

                <th>
                  Actions
                </th>

              </tr>

            </thead>


            <tbody>

              {changes.map(
                (c) => (

                  <tr
                    key={c.id}
                  >

                    <td>

                      {c.source ===
                      "drone" ? (

                        <span
                          className="badge"
                          style={{
                            background:
                              "rgba(255,50,50,0.18)",
                            color:
                              "#ff6666",
                          }}
                        >
                          🚁 DRONE
                        </span>

                      ) : (

                        <span
                          className="badge"
                        >
                          👤 USER
                        </span>

                      )}

                    </td>


                    <td
                      onClick={() =>
                        navigate(
                          `/changes/${c.id}`
                        )
                      }
                    >
                      {c.class_name}
                    </td>


                    <td>

                      <span
                        className={`badge ${c.change_type}`}
                      >
                        {c.change_type}
                      </span>

                    </td>


                    <td>

                      {c.avg_confidence !=
                      null
                        ? (
                            c.avg_confidence *
                            100
                          ).toFixed(1) +
                          "%"
                        : "—"}

                    </td>


                    <td>
                      {c.zone_name ??
                        "—"}
                    </td>


                    <td>
                      {c.priority_score ??
                        "—"}
                    </td>


                    <td>

                      <button
                        className="btn secondary"
                        disabled={
                          busyId === c.id
                        }
                        onClick={() =>
                          runGeo(c.id)
                        }
                        style={{
                          marginRight: 6,
                        }}
                      >
                        Analyze geo
                      </button>


                      <button
                        className="btn secondary"
                        disabled={
                          busyId === c.id
                        }
                        onClick={() =>
                          runScore(c.id)
                        }
                      >
                        Score
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