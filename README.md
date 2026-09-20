# AI City OS

AI City OS is a city incident response and prioritization platform that ingests civic incidents, analyzes their likely impact, estimates priority, and recommends response actions. It combines a FastAPI backend, a React frontend, and a graph-based city model to simulate emergency decision support for urban operations.

## Overview

The application is designed to help city operators:

- capture reported incidents such as flooding, power outages, and road blockages;
- assess severity and confidence using a mock AI analysis layer;
- model direct and secondary impact on services, infrastructure, and neighborhoods;
- prioritize municipal action based on operational risk and population impact;
- assign response teams and track notes, status changes, and activity history.

## Key features

- FastAPI API for incident CRUD and analysis flows
- City graph representation for entity/service relationships
- Severity and priority scoring engines
- Response recommendation generation for emergency workflows
- Incident persistence with JSON-based storage
- Demo scenario data for testing common urban disruptions
- React dashboard frontend for visualizing city-level incident information

## Tech stack

- Backend: Python, FastAPI, Pydantic, NetworkX
- Frontend: React, Vite
- Testing: Pytest
- Environment: Docker-ready project structure

## Project structure

```text
ai-city-os/
├── backend/
│   ├── api/
│   ├── data/
│   ├── graph/
│   ├── models/
│   ├── services/
│   └── main.py
├── demo/
├── frontend/
├── tests/
├── docker-compose.yml
├── requirements.txt
├── README.md
└── .venv/
```

## Backend API

The backend exposes incident endpoints under `/api/incidents`:

- `POST /api/incidents` — create a new incident
- `GET /api/incidents` — list all incidents
- `GET /api/incidents/{incident_id}` — fetch one incident
- `POST /api/incidents/{incident_id}/analyze` — run AI-based analysis
- `GET /api/incidents/{incident_id}/impact` — calculate direct and secondary impact
- `GET /api/incidents/{incident_id}/response` — generate response recommendations
- `PATCH /api/incidents/{incident_id}/status` — update status
- `POST /api/incidents/{incident_id}/notes` — add notes
- `POST /api/incidents/{incident_id}/assign` — assign department/escalation
- `GET /api/incidents/{incident_id}/timeline` — review activity timeline

Health endpoint:

- `GET /health`

## Local setup

### 1) Create and activate a virtual environment

On Windows PowerShell:

```powershell
cd "d:\AI city OS\ai-city-os"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2) Install dependencies

```powershell
pip install -r requirements.txt
```

### 3) Run the backend

```powershell
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:

- http://localhost:8000
- Swagger docs: http://localhost:8000/docs

### 4) Run the frontend

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Then open the local Vite URL shown in the terminal, usually:

- http://localhost:5173

## Running tests

From the project root:

```powershell
pytest
```

This project includes tests for:

- AI incident analysis
- city graph connectivity and entity data
- demo scenario behavior
- FastAPI endpoints
- impact and priority calculations
- response recommendations

## Demo scenarios

The `demo/` folder contains example incident payloads such as:

- `flooding.json`
- `power_outage.json`
- `road_blockage.json`

These can be used to validate the analysis and recommendation logic against realistic city disruption cases.

## Notes

This project is a local MVP and uses a mock AI analyzer rather than a live external AI backend. The architecture is designed to support future expansion with real forecasting, GIS intelligence, and cloud integration.

## License

This project is intended for internal prototype and demonstration use unless otherwise specified by the owning organization.

