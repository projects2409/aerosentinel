import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import MapView from "../components/MapView.jsx";

export default function Dashboard() {
  const [surveys, setSurveys] = useState([]);
  const [changes, setChanges] = useState([]);
  const [ranked, setRanked] = useState([]);
  const [mode, setMode] = useState(null);

  useEffect(() => {
    api.listSurveys().then(setSurveys).catch(() => {});
    api.listChanges().then(setChanges).catch(() => {});
    api.rankedCases().then(setRanked).catch(() => {});
    api.detectionMode().then(setMode).catch(() => {});
  }, []);

  return (
    <>
      <h2>Dashboard</h2>
      <div className="grid" style={{ marginBottom: 18 }}>
        <div className="card">
          <h3>{surveys.length}</h3>
          <div>Surveys uploaded</div>
        </div>
        <div className="card">
          <h3>{changes.length}</h3>
          <div>Detected changes</div>
        </div>
        <div className="card">
          <h3>{ranked.length}</h3>
          <div>Scored cases</div>
        </div>
        <div className="card">
          <h3>{mode?.mock_mode ? "MOCK" : "REAL"}</h3>
          <div>Detection mode</div>
        </div>
      </div>

      <div className="card">
        <h3>Case map</h3>
        <MapView cases={changes} />
      </div>

      <div className="card">
        <h3>Top priority cases</h3>
        {ranked.length === 0 && <p>No scored cases yet — score changes in the Changes tab.</p>}
        {ranked.length > 0 && (
          <table>
            <thead>
              <tr>
                <th>Class</th>
                <th>Type</th>
                <th>Score</th>
              </tr>
            </thead>
            <tbody>
              {ranked.slice(0, 5).map((c) => (
                <tr key={c.id}>
                  <td>
                    <Link to={`/changes/${c.id}`}>{c.class_name}</Link>
                  </td>
                  <td>
                    <span className={`badge ${c.change_type}`}>{c.change_type}</span>
                  </td>
                  <td>{c.priority_score}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}