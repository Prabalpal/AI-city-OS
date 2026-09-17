from __future__ import annotations

from typing import Any

from backend.data.seed_data import load_seed_data
from backend.graph.city_graph import CityGraph
from backend.services.ai_service import MockAIAnalyzer


class ImpactEngine:
    def __init__(self, city_graph: CityGraph | None = None, analyzer: Any | None = None) -> None:
        self.city_graph = city_graph or CityGraph.from_seed_data(load_seed_data())
        self.analyzer = analyzer or MockAIAnalyzer()

    def analyze_incident(self, incident: dict[str, Any]) -> dict[str, Any]:
        analyzed = self.analyzer.analyze_incident(incident)
        root_candidates = self.city_graph.find_nearby_entities(
            self._find_nearest_entity_id(incident["latitude"], incident["longitude"]),
            radius_km=3.0,
        )

        directly_affected = [entity["id"] for entity in root_candidates[:5]]
        connected_ids = []
        for entity in root_candidates:
            connected_ids.extend(self.city_graph.find_connected_entities(entity["id"], max_depth=3))

        unique_connected = []
        seen: set[str] = set()
        for entity_id in connected_ids:
            if entity_id not in seen:
                unique_connected.append(entity_id)
                seen.add(entity_id)

        critical_services = self.city_graph.find_affected_critical_services(
            self._find_nearest_entity_id(incident["latitude"], incident["longitude"]),
            max_depth=3,
        )

        estimated_population = self._estimate_population(unique_connected)
        impact_level = self._calculate_impact_level(len(unique_connected), len(critical_services), analyzed["severity"])
        impact_explanation = self._build_explanation(directly_affected, critical_services, unique_connected)

        return {
            "incident_type": analyzed["incident_type"],
            "severity": analyzed["severity"],
            "confidence": analyzed["confidence"],
            "directly_affected": directly_affected,
            "secondarily_affected": unique_connected,
            "critical_services_affected": critical_services,
            "estimated_population": estimated_population,
            "impact_level": impact_level,
            "impact_explanation": impact_explanation,
        }

    def _find_nearest_entity_id(self, latitude: float, longitude: float) -> str:
        nearest_id = None
        nearest_distance = None

        for entity_id, attrs in self.city_graph.graph.nodes(data=True):
            distance = self.city_graph._haversine_km(latitude, longitude, attrs["latitude"], attrs["longitude"])
            if nearest_distance is None or distance < nearest_distance:
                nearest_distance = distance
                nearest_id = entity_id

        return nearest_id or "ROAD_R1"

    def _estimate_population(self, entity_ids: list[str]) -> int:
        total = 0
        for entity_id in entity_ids:
            entity = self.city_graph.get_entity(entity_id)
            if not entity:
                continue
            metadata = entity.get("metadata", {})
            total += metadata.get("students", 0)
            total += metadata.get("employees", 0)
            total += metadata.get("capacity", 0)
            total += metadata.get("population", 0)
        return total

    def _calculate_impact_level(self, connected_count: int, critical_count: int, severity: int) -> str:
        score = severity * 2 + connected_count + critical_count
        if score >= 15:
            return "critical"
        if score >= 9:
            return "high"
        if score >= 5:
            return "medium"
        return "low"

    def _build_explanation(self, directly_affected: list[str], critical_services: list[str], secondaries: list[str]) -> list[str]:
        explanation: list[str] = []
        if directly_affected:
            explanation.append(f"Primary city assets affected: {', '.join(directly_affected)}")
        if critical_services:
            explanation.append(f"Critical service dependency impacted: {', '.join(critical_services)}")
        if secondaries:
            explanation.append(f"Secondary disruption spreads across nearby connected entities: {', '.join(secondaries[:5])}")
        if not explanation:
            explanation.append("Localized incident with limited citywide disruption.")
        return explanation
