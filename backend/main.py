from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.data.seed_data import load_seed_data
from backend.data.store import load_persisted_incidents_from_db, save_incidents_to_db
from backend.graph.city_graph import CityGraph
from backend.models.incident import Incident, IncidentAssignment, IncidentCreate, IncidentSource, IncidentStatus, NoteCreate
from backend.models.entity import CityEntity
from backend.services.ai_service import MockAIAnalyzer
from backend.services.impact_engine import ImpactEngine
from backend.services.priority_engine import PriorityEngine
from backend.services.response_engine import ResponseEngine

app = FastAPI(title="AI City OS", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

city_graph = CityGraph.from_seed_data(load_seed_data())
analyzer = MockAIAnalyzer()
impact_engine = ImpactEngine(city_graph=city_graph, analyzer=analyzer)
priority_engine = PriorityEngine()
response_engine = ResponseEngine()

PERSISTENCE_PATH = Path(__file__).resolve().parent / "data" / "incidents_store.json"


def load_persisted_incidents() -> dict[str, Incident]:
    if not PERSISTENCE_PATH.exists():
        return {}

    try:
        raw_data = json.loads(PERSISTENCE_PATH.read_text(encoding="utf-8"))
        if not isinstance(raw_data, dict):
            return {}
        return {incident_id: Incident.model_validate(payload) for incident_id, payload in raw_data.items()}
    except (json.JSONDecodeError, TypeError, ValueError):
        return {}


def save_incidents() -> None:
    PERSISTENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {incident_id: incident.model_dump(mode="json") for incident_id, incident in incidents.items()}
    PERSISTENCE_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    save_incidents_to_db(incidents)


incidents: dict[str, Incident] = load_persisted_incidents_from_db() or load_persisted_incidents()


def record_activity(incident: Incident, activity_type: str, message: str) -> None:
    incident.activity.append(
        {
            "type": activity_type,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "ai-city-os"}


@app.post("/api/incidents", response_model=Incident, status_code=status.HTTP_201_CREATED)
def create_incident(payload: IncidentCreate) -> Incident:
    incident_id = str(uuid4())
    source_value = payload.source.value if isinstance(payload.source, IncidentSource) else str(payload.source)
    incident = Incident(
        id=incident_id,
        type=payload.type,
        title=payload.title,
        description=payload.description,
        source=payload.source,
        latitude=payload.latitude,
        longitude=payload.longitude,
        severity=payload.severity,
        confidence=payload.confidence,
        status=IncidentStatus.REPORTED,
        notes=[],
        activity=[],
    )
    record_activity(incident, "created", f"Incident reported by {source_value}")
    incidents[incident_id] = incident
    save_incidents()
    return incident


@app.get("/api/incidents")
def list_incidents() -> list[Incident]:
    return list(incidents.values())


@app.get("/api/incidents/{incident_id}")
def get_incident(incident_id: str) -> Incident:
    incident = incidents.get(incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return incident


@app.post("/api/incidents/{incident_id}/analyze")
def analyze_incident(incident_id: str) -> dict[str, Any]:
    incident = incidents.get(incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    analysis = analyzer.analyze_incident(
        {
            "description": incident.description,
            "type": incident.type,
            "latitude": incident.latitude,
            "longitude": incident.longitude,
        }
    )
    incident.severity = analysis["severity"]
    incident.confidence = analysis["confidence"]
    incident.status = IncidentStatus.ANALYZING
    return analysis


@app.get("/api/incidents/{incident_id}/impact")
def get_incident_impact(incident_id: str) -> dict[str, Any]:
    incident = incidents.get(incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    impact = impact_engine.analyze_incident(
        {
            "description": incident.description,
            "type": incident.type,
            "latitude": incident.latitude,
            "longitude": incident.longitude,
        }
    )
    return impact


@app.get("/api/incidents/{incident_id}/response")
def get_incident_response(incident_id: str) -> dict[str, Any]:
    incident = incidents.get(incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    impact = impact_engine.analyze_incident(
        {
            "description": incident.description,
            "type": incident.type,
            "latitude": incident.latitude,
            "longitude": incident.longitude,
        }
    )
    priority = priority_engine.calculate_priority(
        severity=incident.severity,
        impacted_entities=impact["directly_affected"] + impact["secondarily_affected"],
        critical_services=impact["critical_services_affected"],
        estimated_population=impact["estimated_population"],
        emergency_service_impact=bool(impact["critical_services_affected"]),
    )
    response = response_engine.generate_response(incident.type, impact, priority)
    response["incident_id"] = incident_id
    return response


@app.patch("/api/incidents/{incident_id}/status")
def update_incident_status(incident_id: str, status_update: dict[str, str]) -> Incident:
    incident = incidents.get(incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    status_value = status_update.get("status")
    if status_value is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Status is required")

    try:
        incident.status = IncidentStatus(status_value)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid incident status") from exc

    record_activity(incident, "status_change", f"Status updated to {incident.status}")
    save_incidents()
    return incident


@app.post("/api/incidents/{incident_id}/notes")
def add_incident_note(incident_id: str, payload: NoteCreate) -> dict[str, Any]:
    incident = incidents.get(incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    incident.notes.append(payload.text)
    record_activity(incident, "note", payload.text)
    save_incidents()
    return {"notes": incident.notes, "activity": incident.activity}


@app.post("/api/incidents/{incident_id}/assign")
def assign_incident(incident_id: str, payload: IncidentAssignment) -> dict[str, Any]:
    incident = incidents.get(incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    incident.assigned_department = payload.department
    incident.escalation_level = payload.escalation_level
    incident.status = IncidentStatus.ASSIGNED

    if payload.note:
        incident.notes.append(payload.note)
        record_activity(incident, "note", payload.note)

    record_activity(incident, "assignment", f"Assigned to {payload.department} at escalation level {payload.escalation_level}")
    save_incidents()
    return {
        "assigned_department": incident.assigned_department,
        "escalation_level": incident.escalation_level,
        "status": incident.status,
        "notes": incident.notes,
        "activity": incident.activity,
    }


@app.get("/api/incidents/{incident_id}/timeline")
def get_incident_timeline(incident_id: str) -> dict[str, Any]:
    incident = incidents.get(incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    timeline = []
    for event in incident.activity:
        timeline.append(
            {
                "type": event.get("type", "activity"),
                "message": event.get("message", "Update"),
                "timestamp": event.get("timestamp", incident.created_at.isoformat()),
            }
        )

    if not timeline:
        timeline.append(
            {
                "type": "created",
                "message": f"Incident reported by {incident.source}",
                "timestamp": incident.created_at.isoformat(),
            }
        )

    timeline.sort(key=lambda item: item["timestamp"])
    sla_minutes = max(15, 90 - (incident.severity * 10) + (incident.escalation_level or 0) * 5)
    return {
        "incident_id": incident_id,
        "sla_minutes": sla_minutes,
        "assigned_department": incident.assigned_department,
        "timeline": timeline,
    }


@app.post("/api/incidents/{incident_id}/simulate")
def simulate_incident_dependencies(incident_id: str, payload: dict[str, str] | None = None) -> dict[str, Any]:
    incident = incidents.get(incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    scenario = (payload or {}).get("scenario", "default")
    impact = impact_engine.analyze_incident(
        {
            "description": incident.description,
            "type": incident.type,
            "latitude": incident.latitude,
            "longitude": incident.longitude,
        }
    )

    dependencies = list(dict.fromkeys(impact.get("critical_services_affected", []) + impact.get("directly_affected", []) + impact.get("secondarily_affected", [])))
    if not dependencies:
        dependencies = [incident.type, "city_operations_center"]

    incident.service_dependencies = dependencies
    event = {
        "type": "service_simulation",
        "scenario": scenario,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "details": dependencies,
    }
    incident.simulation_history.append(event)
    record_activity(incident, "service_simulation", f"Service dependency simulation for scenario '{scenario}' completed")
    save_incidents()

    return {
        "service_dependencies": incident.service_dependencies,
        "simulation_history": incident.simulation_history,
        "estimated_population": impact["estimated_population"],
        "impact_level": impact["impact_level"],
        "scenario": scenario,
        "status": incident.status,
        "activity": incident.activity,
    }


@app.get("/api/entities")
def list_entities() -> list[CityEntity]:
    return [CityEntity(**attrs) for _, attrs in city_graph.graph.nodes(data=True)]


@app.get("/api/entities/{entity_id}")
def get_entity(entity_id: str) -> CityEntity:
    entity = city_graph.get_entity(entity_id)
    if entity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entity not found")
    return CityEntity(**entity)


@app.get("/api/entities/{entity_id}/connections")
def get_entity_connections(entity_id: str) -> list[dict[str, Any]]:
    if entity_id not in city_graph.graph.nodes:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entity not found")
    return city_graph.find_entity_connections(entity_id)


@app.get("/api/dashboard/summary")
def dashboard_summary() -> dict[str, Any]:
    active = [incident for incident in incidents.values() if incident.status != IncidentStatus.RESOLVED]
    critical = [incident for incident in active if incident.severity >= 4]
    all_entities = [CityEntity(**attrs) for _, attrs in city_graph.graph.nodes(data=True)]
    impacted = sum(1 for entity in all_entities if entity.type in {"hospital", "school", "power_station", "drainage_zone"})
    total_population = sum(
        int(entity.metadata.get("students", 0) or 0) + int(entity.metadata.get("employees", 0) or 0) + int(entity.metadata.get("population", 0) or 0)
        for entity in all_entities
    )
    return {
        "total_active_incidents": len(active),
        "critical_incidents": len(critical),
        "affected_services": impacted,
        "estimated_affected_population": total_population,
        "resolved_incidents": sum(1 for incident in incidents.values() if incident.status == IncidentStatus.RESOLVED),
    }


@app.get("/api/dashboard/incidents")
def dashboard_incidents() -> list[Incident]:
    return list(incidents.values())


@app.get("/api/dashboard/map")
def dashboard_map() -> dict[str, Any]:
    entities = [CityEntity(**attrs) for _, attrs in city_graph.graph.nodes(data=True)]
    incidents_payload = [
        {
            "id": incident.id,
            "title": incident.title,
            "type": incident.type,
            "latitude": incident.latitude,
            "longitude": incident.longitude,
            "severity": incident.severity,
            "status": incident.status,
        }
        for incident in incidents.values()
    ]
    return {"entities": [entity.model_dump(mode="json") for entity in entities], "incidents": incidents_payload}
