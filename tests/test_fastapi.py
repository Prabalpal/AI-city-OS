from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_health_route():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_and_get_incident():
    response = client.post(
        "/api/incidents",
        json={
            "type": "flooding",
            "title": "Flooding near central hospital",
            "description": "Severe waterlogging near the main hospital road",
            "source": "citizen",
            "latitude": 23.825,
            "longitude": 90.413,
            "severity": 4,
            "confidence": 0.9,
        },
    )

    assert response.status_code == 201
    payload = response.json()
    incident_id = payload["id"]

    detail = client.get(f"/api/incidents/{incident_id}")
    assert detail.status_code == 200
    assert detail.json()["title"] == "Flooding near central hospital"


def test_dashboard_summary():
    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200
    payload = response.json()
    assert "total_active_incidents" in payload
    assert "critical_incidents" in payload


def test_incident_note_and_activity_history():
    response = client.post(
        "/api/incidents",
        json={
            "type": "power_outage",
            "title": "Transformer failure",
            "description": "Multiple blocks are without power",
            "source": "sensor",
            "latitude": 23.81,
            "longitude": 90.41,
            "severity": 5,
            "confidence": 0.95,
        },
    )
    assert response.status_code == 201
    incident_id = response.json()["id"]

    update = client.patch(
        f"/api/incidents/{incident_id}/status",
        json={"status": "assigned"},
    )
    assert update.status_code == 200

    note = client.post(
        f"/api/incidents/{incident_id}/notes",
        json={"text": "Utility crew dispatched to substation"},
    )
    assert note.status_code == 200
    payload = note.json()
    assert "notes" in payload
    assert any("Utility crew dispatched to substation" in item for item in payload["notes"])
    assert "activity" in payload
    assert payload["activity"][-1]["type"] == "note"


def test_assign_incident_to_department_and_escalate():
    response = client.post(
        "/api/incidents",
        json={
            "type": "power_outage",
            "title": "Grid failure at station 5",
            "description": "Critical transformer failure affecting multiple neighborhoods",
            "source": "system",
            "latitude": 23.82,
            "longitude": 90.42,
            "severity": 5,
            "confidence": 0.98,
        },
    )
    assert response.status_code == 201
    incident_id = response.json()["id"]

    result = client.post(
        f"/api/incidents/{incident_id}/assign",
        json={
            "department": "Utilities",
            "escalation_level": 3,
            "note": "Escalated to utility emergency response",
        },
    )

    assert result.status_code == 200
    payload = result.json()
    assert payload["assigned_department"] == "Utilities"
    assert payload["escalation_level"] == 3
    assert payload["status"] == "assigned"
    assert any("Utilities" in entry["message"] for entry in payload["activity"])


def test_service_dependency_simulation_history():
    response = client.post(
        "/api/incidents",
        json={
            "type": "power_outage",
            "title": "Regional power failure",
            "description": "Main substation outage affecting critical services",
            "source": "sensor",
            "latitude": 23.82,
            "longitude": 90.42,
            "severity": 5,
            "confidence": 0.97,
        },
    )
    incident_id = response.json()["id"]

    result = client.post(
        f"/api/incidents/{incident_id}/simulate",
        json={"scenario": "grid_failure"},
    )

    assert result.status_code == 200
    payload = result.json()
    assert "service_dependencies" in payload
    assert "simulation_history" in payload
    assert payload["service_dependencies"]
    assert payload["simulation_history"][-1]["type"] == "service_simulation"


def test_sqlite_round_trip_persistence():
    from backend.data.store import load_persisted_incidents_from_db, save_incidents_to_db
    from backend.models.incident import Incident, IncidentSource, IncidentStatus

    incident = Incident(
        id="sqlite-test-1",
        type="fire",
        title="Warehouse fire",
        description="Smoke near warehouse district",
        source=IncidentSource.CAMERA,
        latitude=23.81,
        longitude=90.44,
        severity=4,
        confidence=0.91,
        status=IncidentStatus.REPORTED,
    )

    save_incidents_to_db({incident.id: incident})
    restored = load_persisted_incidents_from_db()

    assert incident.id in restored
    assert restored[incident.id].title == "Warehouse fire"


def test_incident_timeline_and_sla_tracking():
    response = client.post(
        "/api/incidents",
        json={
            "type": "medical_emergency",
            "title": "Ambulance access blocked",
            "description": "Emergency route blocked near city clinic",
            "source": "citizen",
            "latitude": 23.79,
            "longitude": 90.41,
            "severity": 3,
            "confidence": 0.85,
        },
    )
    incident_id = response.json()["id"]

    client.patch(
        f"/api/incidents/{incident_id}/status",
        json={"status": "assigned"},
    )

    timeline = client.get(f"/api/incidents/{incident_id}/timeline")
    assert timeline.status_code == 200
    payload = timeline.json()
    assert payload["sla_minutes"] > 0
    assert "timeline" in payload
    assert payload["timeline"][0]["type"] in {"created", "status_change", "note", "assignment", "service_simulation"}
