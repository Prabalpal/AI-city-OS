from backend.services.impact_engine import ImpactEngine


def test_impact_engine_identifies_hospital_and_school_dependencies():
    engine = ImpactEngine()
    result = engine.analyze_incident({
        "description": "Severe waterlogging near the main hospital road",
        "type": "waterlogging",
        "latitude": 23.825,
        "longitude": 90.413,
    })

    assert result["impact_level"] in {"high", "critical"}
    assert "HOSPITAL_H1" in result["directly_affected"] or "HOSPITAL_H1" in result["secondarily_affected"]
    assert "SCHOOL_S1" in result["secondarily_affected"] or "SCHOOL_S1" in result["directly_affected"]
    assert result["estimated_population"] > 0


def test_impact_engine_flags_critical_service_outage():
    engine = ImpactEngine()
    result = engine.analyze_incident({
        "description": "Power station failure affecting central hospital and offices",
        "type": "power_outage",
        "latitude": 23.852,
        "longitude": 90.398,
    })

    assert result["impact_level"] in {"high", "critical"}
    assert "HOSPITAL_H1" in result["critical_services_affected"] or "HOSPITAL_H1" in result["secondarily_affected"]
    assert result["estimated_population"] > 1000
