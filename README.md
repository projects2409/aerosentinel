# AeroSentinel

AeroSentinel is a full-stack web application for map-based monitoring,
geospatial analysis, temporal change analysis, and priority scoring.

The project includes a JavaScript frontend and a Python backend that
work together to present geospatial information and analysis results.

## Features

- Interactive map-based interface
- Geospatial analysis workflows
- Temporal change analysis
- Priority scoring API
- Frontend and backend integration
- Support for configured geospatial data
- Optional model weights for supported detection workflows

Features available at runtime depend on the backend configuration,
data files, and any required model weights.

## Technology Stack

### Frontend
- JavaScript
- React
- Vite
- Leaflet

### Backend
- Python
- FastAPI
- Uvicorn
- NumPy
- Pandas
- GeoPandas
- Shapely
- OpenCV

Additional dependencies are listed in `backend/requirement.txt`.

## Project Structure

```text
aerosentinel/
├── backend/
│   ├── app/
│   ├── weights/             # Local model weights
│   └── requirement.txt
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.js
├── sample_data/
│   └── boundaries.geojson
├── .gitignore
└── README.md