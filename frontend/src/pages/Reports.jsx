import {
  useEffect,
  useState,
} from "react";

import { api } from "../api";


export default function Reports() {

  const [
    reports,
    setReports,
  ] = useState([]);

  const [
    error,
    setError,
  ] = useState(null);


  const load = () => {

    api
      .listReports()
      .then(setReports)
      .catch((e) =>
        setError(e.message)
      );

  };


  useEffect(() => {
    load();
  }, []);


  return (

    <>

      <h2>
        Reports
      </h2>


      <div className="card">

        <p
          style={{
            color:
              "var(--muted)",
            fontSize: 13,
          }}
        >
          Reports generated from
          user-submitted cases and
          automatically detected drone
          events.
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


        {reports.length === 0 && (

          <p>
            No reports generated yet.
          </p>

        )}


        {reports.length > 0 && (

          <table>

            <thead>

              <tr>

                <th>
                  Source
                </th>

                <th>
                  Report ID
                </th>

                <th>
                  Change ID
                </th>

                <th>
                  Created
                </th>

                <th>
                </th>

              </tr>

            </thead>


            <tbody>

              {reports.map(
                (r) => (

                  <tr
                    key={r.id}
                  >

                    <td>

                      {r.source ===
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


                    <td>
                      {r.id}
                    </td>


                    <td>
                      {r.change_id}
                    </td>


                    <td>
                      {new Date(
                        r.created_at
                      ).toLocaleString()}
                    </td>


                    <td>

                      <a
                        className="btn secondary"
                        href={
                          api.reportDownloadUrl(
                            r.id
                          )
                        }
                        target="_blank"
                        rel="noreferrer"
                      >
                        Download
                      </a>

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