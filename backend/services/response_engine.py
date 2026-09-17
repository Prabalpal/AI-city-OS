from __future__ import annotations

from typing import Any

from backend.models.response import ResponsePriority, ResponseStatus, ResponseTask


class ResponseEngine:
    def __init__(self) -> None:
        self.department_rules = {
            "waterlogging": [
                ("Drainage", "Dispatch drainage response team", ResponsePriority.CRITICAL),
                ("Traffic Control", "Manage traffic and activate alternate route", ResponsePriority.HIGH),
                ("Public Works", "Inspect culverts and stormwater channels", ResponsePriority.HIGH),
            ],
            "power_outage": [
                ("Utilities", "Dispatch power restoration crew", ResponsePriority.CRITICAL),
                ("Hospital Administration", "Notify hospital about backup power and emergency routing", ResponsePriority.CRITICAL),
                ("Government Operations", "Coordinate emergency communications", ResponsePriority.HIGH),
            ],
            "road_blockage": [
                ("Traffic Control", "Deploy detour signage and lane management", ResponsePriority.HIGH),
                ("Emergency Services", "Prioritize ambulance access corridor", ResponsePriority.CRITICAL),
                ("Public Works", "Clear obstruction and inspect road integrity", ResponsePriority.HIGH),
            ],
        }

    def generate_response(self, incident_type: str, impact_report: dict[str, Any], priority_result: dict[str, Any]) -> dict[str, Any]:
        normalized_type = (incident_type or "incident").lower()
        base_rules = self.department_rules.get(normalized_type, [
            ("Operations Center", "Assess response coordination", ResponsePriority.MEDIUM),
            ("Public Works", "Review immediate service needs", ResponsePriority.MEDIUM),
        ])

        tasks = []
        for department, action, priority in base_rules:
            tasks.append(
                ResponseTask(
                    department=department,
                    action=action,
                    priority=priority,
                    status=ResponseStatus.PENDING,
                )
            )

        summary = self._build_summary(normalized_type, priority_result)
        responsible_departments = list({task.department for task in tasks})
        recommended_actions = [task.action for task in tasks]
        urgency = self._derive_urgency(priority_result.get("priority", "MEDIUM"))

        return {
            "tasks": [task.model_dump(mode="json") for task in tasks],
            "response_summary": summary,
            "responsible_departments": responsible_departments,
            "recommended_actions": recommended_actions,
            "estimated_urgency": urgency,
            "priority": priority_result.get("priority", "MEDIUM"),
        }

    def _build_summary(self, incident_type: str, priority_result: dict[str, Any]) -> str:
        priority = priority_result.get("priority", "MEDIUM")
        if incident_type == "waterlogging":
            return f"Flood response is {priority.lower()} priority due to road and service disruption."
        if incident_type == "power_outage":
            return f"Power recovery is {priority.lower()} priority due to critical dependency risk."
        if incident_type == "road_blockage":
            return f"Road clearance is {priority.lower()} priority due to access and transit disruption."
        return f"Operational response is {priority.lower()} priority pending field verification."

    def _derive_urgency(self, priority: str) -> str:
        urgent_map = {
            "CRITICAL": "immediate",
            "HIGH": "rapid",
            "MEDIUM": "scheduled",
            "LOW": "monitor",
        }
        return urgent_map.get(priority, "scheduled")
