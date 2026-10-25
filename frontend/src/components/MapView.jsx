import "leaflet/dist/leaflet.css";

import L from "leaflet";

import {
  useEffect,
  useState,
} from "react";

import {
  GeoJSON,
  MapContainer,
  Marker,
  Popup,
  TileLayer,
} from "react-leaflet";

import { api } from "../api";


// ------------------------------------------------------------
// Normal marker
// ------------------------------------------------------------

delete L.Icon.Default.prototype._getIconUrl;

L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",

  iconUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",

  shadowUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});


// ------------------------------------------------------------
// Drone marker
// ------------------------------------------------------------

const droneIcon =
  new L.Icon({
    iconUrl:
      "https://maps.google.com/mapfiles/ms/icons/red-dot.png",

    iconSize: [
      32,
      32,
    ],

    iconAnchor: [
      16,
      32,
    ],

    popupAnchor: [
      0,
      -30,
    ],
  });


export default function MapView({
  cases = [],
  center = [
    29.863,
    77.875,
  ],
  height = 420,
}) {

  const [
    boundaries,
    setBoundaries,
  ] = useState(null);


  useEffect(() => {

    api
      .getBoundaries()
      .then((raw) =>
        setBoundaries(
          typeof raw === "string"
            ? JSON.parse(raw)
            : raw
        )
      )
      .catch(() =>
        setBoundaries(null)
      );

  }, []);


  return (

    <MapContainer
      center={center}
      zoom={14}
      style={{
        height,
        width: "100%",
      }}
    >

      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution="&copy; OpenStreetMap contributors"
      />


      {boundaries && (

        <GeoJSON
          data={boundaries}
          style={{
            color:
              "#f5b342",
            weight: 1,
            fillOpacity: 0.08,
          }}
        />

      )}


      {cases
        .filter(
          (c) =>
            c.lat != null &&
            c.lon != null
        )
        .map((c) => {

          const isDrone =
            c.source === "drone";


          return (

            <Marker
              key={c.id}
              position={[
                c.lat,
                c.lon,
              ]}
              icon={
                isDrone
                  ? droneIcon
                  : new L.Icon.Default()
              }
            >

              <Popup>

                <strong>
                  {isDrone
                    ? "🚁 Drone Detection"
                    : "👤 User Report"}
                </strong>

                <br />

                <strong>
                  {c.class_name}
                </strong>

                {" — "}

                {c.change_type}

                <br />

                Source:{" "}

                {isDrone
                  ? "Drone / CDAC YOLO"
                  : "User"}

                <br />

                Confidence:{" "}

                {c.avg_confidence != null
                  ? (
                      c.avg_confidence *
                      100
                    ).toFixed(1) + "%"
                  : "—"}

                <br />

                Priority:{" "}

                {c.priority_score ??
                  "not scored"}

                <br />

                Zone:{" "}

                {c.zone_name ??
                  "unassigned"}

              </Popup>

            </Marker>

          );

        })}

    </MapContainer>
  );
}