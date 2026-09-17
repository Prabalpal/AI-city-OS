from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class AIAnalyzer(ABC):
    @abstractmethod
    def analyze_incident(self, raw_incident: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class MockAIAnalyzer(AIAnalyzer):
    def analyze_incident(self, raw_incident: dict[str, Any]) -> dict[str, Any]:
        description = (raw_incident.get("description") or "").strip().lower()
        incident_type = (raw_incident.get("type") or "incident").strip().lower()
        latitude = float(raw_incident.get("latitude", 0.0))
        longitude = float(raw_incident.get("longitude", 0.0))

        normalized_type = self._normalize_type(incident_type, description)
        severity = self._estimate_severity(normalized_type, description)
        confidence = self._estimate_confidence(severity, description)
        summary = self._build_summary(normalized_type, description)
        possible_impact = self._build_possible_impact(normalized_type)

        return {
            "incident_type": normalized_type,
            "severity": severity,
            "confidence": confidence,
            "summary": summary,
            "possible_impact": possible_impact,
            "latitude": latitude,
            "longitude": longitude,
            "raw_type": incident_type,
        }

    def _normalize_type(self, incident_type: str, description: str) -> str:
        if "flood" in description or incident_type == "flooding" or incident_type == "waterlogging":
            return "waterlogging"
        if "power" in description or incident_type == "power_outage" or incident_type == "outage":
            return "power_outage"
        if "road" in description or "block" in description or incident_type == "road_blockage":
            return "road_blockage"
        if "fire" in description:
            return "fire"
        if "medical" in description or "hospital" in description:
            return "medical_emergency"
        return incident_type or "incident"

    def _estimate_severity(self, incident_type: str, description: str) -> int:
        keywords = {
            "waterlogging": 4,
            "power_outage": 5,
            "road_blockage": 3,
            "fire": 5,
            "medical_emergency": 4,
        }
        score = keywords.get(incident_type, 3)
        if "severe" in description or "critical" in description:
            score = min(score + 1, 5)
        if "minor" in description:
            score = max(score - 1, 1)
        return score

    def _estimate_confidence(self, severity: int, description: str) -> float:
        base = 0.72 + (severity * 0.05)
        if "severe" in description or "critical" in description:
            base += 0.08
        return round(min(base, 0.99), 2)

    def _build_summary(self, incident_type: str, description: str) -> str:
        if incident_type == "waterlogging":
            return "Severe waterlogging affecting a major road and nearby civic services"
        if incident_type == "power_outage":
            return "Power infrastructure disruption with risk to critical healthcare and government services"
        if incident_type == "road_blockage":
            return "Road obstruction disrupting access for transit and emergency corridors"
        if incident_type == "medical_emergency":
            return "Medical emergency impacting high-priority care access"
        if not description:
            return f"Unstructured {incident_type} report requiring review"
        return f"Incident classified as {incident_type} with localized disruption risk"

    def _build_possible_impact(self, incident_type: str) -> list[str]:
        impact_map = {
            "waterlogging": ["road_access", "hospital_access", "school_access", "drainage_capacity"],
            "power_outage": ["hospital_power", "government_operations", "residential_lighting", "transport_signal"],
            "road_blockage": ["road_access", "bus_route", "school_access", "ambulance_route"],
            "fire": ["building_evacuation", "road_access", "utility_risk"],
            "medical_emergency": ["hospital_access", "ambulance_route", "critical_care_capacity"],
        }
        return impact_map.get(incident_type, ["road_access", "nearby_services"])


class BedrockAIAnalyzer(AIAnalyzer):
    def analyze_incident(self, raw_incident: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("Bedrock integration is not implemented in this local MVP.")
