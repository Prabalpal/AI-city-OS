from __future__ import annotations

from typing import Any


class PriorityEngine:
    def __init__(self) -> None:
        self.factor_points = {
            "severity": 2,
            "critical_facility": 5,
            "school": 2,
            "multiple_entities": 2,
            "population_over_1000": 2,
            "emergency_service_impact": 3,
        }

    def calculate_priority(self, severity: int, impacted_entities: list[str], critical_services: list[str], estimated_population: int, emergency_service_impact: bool = False) -> dict[str, Any]:
        factors: list[dict[str, Any]] = []
        score = 0

        if severity:
            severity_points = severity * self.factor_points["severity"]
            score += severity_points
            factors.append({"factor": "Incident severity", "points": severity_points})

        if critical_services:
            critical_points = len(critical_services) * self.factor_points["critical_facility"]
            score += critical_points
            factors.append({"factor": "Critical facility affected", "points": critical_points})

        school_count = sum(1 for entity in impacted_entities if entity.startswith("SCHOOL_"))
        if school_count:
            school_points = school_count * self.factor_points["school"]
            score += school_points
            factors.append({"factor": "School affected", "points": school_points})

        if len(impacted_entities) > 2:
            multi_points = self.factor_points["multiple_entities"]
            score += multi_points
            factors.append({"factor": "Multiple entities affected", "points": multi_points})

        if estimated_population > 1000:
            pop_points = self.factor_points["population_over_1000"]
            score += pop_points
            factors.append({"factor": "Population impact above 1000", "points": pop_points})

        if emergency_service_impact:
            emergency_points = self.factor_points["emergency_service_impact"]
            score += emergency_points
            factors.append({"factor": "Emergency service impact", "points": emergency_points})

        priority = self._score_to_priority(score)
        explanation = self._build_explanation(priority, factors)

        return {
            "score": score,
            "priority": priority,
            "factors": factors,
            "explanation": explanation,
        }

    def _score_to_priority(self, score: int) -> str:
        if score >= 18:
            return "CRITICAL"
        if score >= 12:
            return "HIGH"
        if score >= 7:
            return "MEDIUM"
        return "LOW"

    def _build_explanation(self, priority: str, factors: list[dict[str, Any]]) -> str:
        if priority == "CRITICAL":
            return "Priority increased because a critical healthcare or emergency dependency is affected, with multiple city assets under disruption."
        if priority == "HIGH":
            return "Priority increased because the event affects multiple services and public accessibility across the city."
        if priority == "MEDIUM":
            return "Priority is moderate due to partial service disruption and localized impact."
        return "Priority remains low because the event has limited scope and low disruption risk."
