from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class IncidentSource(str, Enum):
    CITIZEN = "citizen"
    SENSOR = "sensor"
    CAMERA = "camera"
    GOVERNMENT = "government"
    SYSTEM = "system"


class IncidentStatus(str, Enum):
    REPORTED = "reported"
    ANALYZING = "analyzing"
    ACTIVE = "active"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"


class IncidentNote(BaseModel):
    text: str = Field(..., min_length=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Incident(BaseModel):
    model_config = ConfigDict(use_enum_values=True, validate_assignment=True)

    id: str = Field(..., min_length=1)
    type: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    source: IncidentSource
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    severity: int = Field(..., ge=1, le=5)
    confidence: float = Field(..., ge=0.0, le=1.0)
    status: IncidentStatus = IncidentStatus.REPORTED
    assigned_department: str | None = None
    escalation_level: int | None = Field(default=None, ge=1, le=5)
    service_dependencies: list[str] = Field(default_factory=list)
    simulation_history: list[dict[str, Any]] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    activity: list[dict[str, str]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class IncidentCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    type: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    source: IncidentSource = IncidentSource.CITIZEN
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    severity: int = Field(default=3, ge=1, le=5)
    confidence: float = Field(default=0.75, ge=0.0, le=1.0)


class NoteCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=500)


class IncidentAssignment(BaseModel):
    department: str = Field(..., min_length=1, max_length=120)
    escalation_level: int = Field(default=1, ge=1, le=5)
    note: str | None = Field(default=None, max_length=500)
