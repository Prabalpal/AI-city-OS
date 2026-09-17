from backend.services.response_engine import ResponseEngine


def test_response_engine_generates_waterlogging_tasks():
    engine = ResponseEngine()
    result = engine.generate_response(
        incident_type="waterlogging",
        impact_report={"impact_level": "high"},
        priority_result={"priority": "CRITICAL"},
    )

    assert result["priority"] == "CRITICAL"
    assert result["estimated_urgency"] == "immediate"
    assert any(task["department"] == "Drainage" for task in result["tasks"])
    assert any("traffic" in task["action"].lower() for task in result["tasks"])


def test_response_engine_generates_power_outage_tasks():
    engine = ResponseEngine()
    result = engine.generate_response(
        incident_type="power_outage",
        impact_report={"impact_level": "critical"},
        priority_result={"priority": "CRITICAL"},
    )

    assert result["estimated_urgency"] == "immediate"
    assert any(task["department"] == "Utilities" for task in result["tasks"])
    assert any("hospital" in task["action"].lower() for task in result["tasks"])
