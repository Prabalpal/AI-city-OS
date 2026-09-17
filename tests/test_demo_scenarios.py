import json
from pathlib import Path

from backend.services.ai_service import MockAIAnalyzer
from backend.services.impact_engine import ImpactEngine
from backend.services.priority_engine import PriorityEngine
from backend.services.response_engine import ResponseEngine


def _load_demo(name: str) -> dict:
    file_path = Path(__file__).resolve().parents[1] / "demo" / f"{name}.json"
    return json.loads(file_path.read_text(encoding="utf-8"))


def test_flooding_demo_predicts_hospital_impact():
    scenario = _load_demo("flooding")
    analyzer = MockAIAnalyzer()
    impact = ImpactEngine().analyze_incident({
        "description": scenario["description"],
        "type": scenario["type"],
        "latitude": scenario["latitude"],
        "longitude": scenario["longitude"],
    })
    priority = PriorityEngine().calculate_priority(
        severity=analyzer.analyze_incident({
            "description": scenario["description"],
            "type": scenario["type"],
            "latitude": scenario["latitude"],
            "longitude": scenario["longitude"],
        })["severity"],
        impacted_entities=impact["directly_affected"] + impact["secondarily_affected"],
        critical_services=impact["critical_services_affected"],
        estimated_population=impact["estimated_population"],
        emergency_service_impact=bool(impact["critical_services_affected"]),
    )

    assert "HOSPITAL_H1" in impact["secondarily_affected"] or "HOSPITAL_H1" in impact["directly_affected"]
    assert priority["priority"] in {"HIGH", "CRITICAL"}


def test_power_outage_demo_increases_priority():
    scenario = _load_demo("power_outage")
    impact = ImpactEngine().analyze_incident({
        "description": scenario["description"],
        "type": scenario["type"],
        "latitude": scenario["latitude"],
        "longitude": scenario["longitude"],
    })
    priority = PriorityEngine().calculate_priority(
        severity=5,
        impacted_entities=impact["directly_affected"] + impact["secondarily_affected"],
        critical_services=impact["critical_services_affected"],
        estimated_population=impact["estimated_population"],
        emergency_service_impact=True,
    )

    assert priority["priority"] == "CRITICAL"
    assert "HOSPITAL_H1" in impact["secondarily_affected"] or "HOSPITAL_H1" in impact["critical_services_affected"]


def test_road_blockage_demo_recommends_routes():
    scenario = _load_demo("road_blockage")
    impact = ImpactEngine().analyze_incident({
        "description": scenario["description"],
        "type": scenario["type"],
        "latitude": scenario["latitude"],
        "longitude": scenario["longitude"],
    })
    response = ResponseEngine().generate_response(
        scenario["type"],
        impact,
        {"priority": "HIGH"},
    )

    assert "HOSPITAL_H1" in impact["secondarily_affected"] or "HOSPITAL_H1" in impact["directly_affected"]
    assert response["estimated_urgency"] in {"rapid", "immediate"}
    assert len(response["recommended_actions"]) >= 2
