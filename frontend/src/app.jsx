import { Route, Routes } from "react-router-dom";

import Nav from "./components/nav.jsx";

import CaseDetail from "./pages/CaseDetail.jsx";
import Changes from "./pages/Changes.jsx";
import Dashboard from "./pages/dashboard.jsx";
import Detection from "./pages/Detection.jsx";
import Reports from "./pages/Reports.jsx";
import Surveys from "./pages/surveys.jsx";


export default function App() {
  return (
    <div className="app-shell">

      <Nav />

      <div className="main">

        <div className="prototype-banner">
          AeroSentinel Prototype — CDAC YOLO drone monitoring,
          temporal change detection and automated rescue reporting.
        </div>

        <Routes>

          <Route
            path="/"
            element={<Dashboard />}
          />

          <Route
            path="/surveys"
            element={<Surveys />}
          />

          <Route
            path="/detection"
            element={<Detection />}
          />

          <Route
            path="/changes"
            element={<Changes />}
          />

          <Route
            path="/changes/:id"
            element={<CaseDetail />}
          />

          <Route
            path="/reports"
            element={<Reports />}
          />

        </Routes>

      </div>

    </div>
  );
}