from backend.services.ai_service import MockAIAnalyzer


def test_mock_ai_analyzer_handles_flooding_incident():
    analyzer = MockAIAnalyzer()
    result = analyzer.analyze_incident({
        "description": "Severe waterlogging near the main hospital road",
        "type": "waterlogging",
        "latitude": 23.83,
        "longitude": 91.28,
    })

    assert result["incident_type"] == "waterlogging"
    assert result["severity"] >= 4
    assert result["confidence"] > 0.7
    assert "hospital_access" in result["possible_impact"]
    assert "school_access" in result["possible_impact"]


def test_mock_ai_analyzer_handles_power_outage():
    analyzer = MockAIAnalyzer()
    result = analyzer.analyze_incident({
        "description": "Power station failure affecting central hospital and offices",
        "type": "power_outage",
        "latitude": 23.82,
        "longitude": 90.42,
    })

    assert result["incident_type"] == "power_outage"
    assert result["severity"] >= 4
    assert "hospital_power" in result["possible_impact"]
    assert "government_operations" in result["possible_impact"]
