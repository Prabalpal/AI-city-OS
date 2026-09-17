from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ResponsePriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ResponseStatus(str, Enum):
    PENDING = "pending"
    DISPATCHED = "dispatched"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"


class ResponseTask(BaseModel):
    model_config = ConfigDict(use_enum_values=True, validate_assignment=True)

    department: str = Field(..., min_length=1)
    action: str = Field(..., min_length=1)
    priority: ResponsePriority = ResponsePriority.MEDIUM
    status: ResponseStatus = ResponseStatus.PENDING
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    incident_id: str | None = None
