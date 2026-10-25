import { NavLink } from "react-router-dom";


const links = [
  {
    to: "/",
    label: "Dashboard",
    end: true,
  },
  {
    to: "/surveys",
    label: "Surveys",
  },
  {
    to: "/detection",
    label: "Detection",
  },
  {
    to: "/changes",
    label: "Changes",
  },
  {
    to: "/reports",
    label: "Reports",
  },
];


export default function Nav() {
  return (
    <div className="sidebar">

      <h1>AeroSentinel</h1>

      <p className="tagline">
        Temporal Aerial Intelligence — Prototype
      </p>

      {links.map((link) => (
        <NavLink
          key={link.to}
          to={link.to}
          end={link.end}
          className={({ isActive }) =>
            "nav-link" +
            (isActive ? " active" : "")
          }
        >
          {link.label}
        </NavLink>
      ))}

      <div
        style={{
          marginTop: 20,
          paddingTop: 15,
          borderTop: "1px solid rgba(255,255,255,0.1)",
        }}
      >

        <div
          style={{
            fontSize: 11,
            color: "var(--muted)",
            marginBottom: 8,
            textTransform: "uppercase",
            letterSpacing: 1,
          }}
        >
          AI Monitoring
        </div>

        <NavLink
          to="/detection"
          className={({ isActive }) =>
            "nav-link drone-nav" +
            (isActive ? " active" : "")
          }
        >
          🚁 Drone Monitoring
        </NavLink>

      </div>

    </div>
  );
}