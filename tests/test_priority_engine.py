from backend.services.priority_engine import PriorityEngine


def test_priority_engine_critical_for_hospital_power_outage():
    engine = PriorityEngine()
    result = engine.calculate_priority(
        severity=5,
        impacted_entities=["ROAD_R1", "HOSPITAL_H1", "SCHOOL_S1", "BUS_B1"],
        critical_services=["HOSPITAL_H1"],
        estimated_population=1800,
        emergency_service_impact=True,
    )

    assert result["score"] > 0
    assert result["priority"] == "CRITICAL"
    assert any(factor["factor"] == "Critical facility affected" for factor in result["factors"])
    assert "critical" in result["explanation"].lower()


def test_priority_engine_medium_for_localized_issue():
    engine = PriorityEngine()
    result = engine.calculate_priority(
        severity=2,
        impacted_entities=["ROAD_R4"],
        critical_services=[],
        estimated_population=500,
        emergency_service_impact=False,
    )

    assert result["priority"] in {"LOW", "MEDIUM"}
    assert result["score"] >= 0
