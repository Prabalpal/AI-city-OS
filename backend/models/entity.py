from __future__ import annotations

from typing import Any
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class EntityType(str, Enum):
    ROAD = "road"
    HOSPITAL = "hospital"
    SCHOOL = "school"
    GOVERNMENT_OFFICE = "government_office"
    POWER_STATION = "power_station"
    DRAINAGE_ZONE = "drainage_zone"
    BUS_ROUTE = "bus_route"
    CITY_ZONE = "city_zone"


class EntityStatus(str, Enum):
    ACTIVE = "active"
    DEGRADED = "degraded"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"


class CityEntity(BaseModel):
    model_config = ConfigDict(use_enum_values=True, validate_assignment=True)

    id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    type: EntityType
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    zone: str = Field(..., min_length=1)
    status: EntityStatus = EntityStatus.ACTIVE
    metadata: dict[str, Any] = Field(default_factory=dict)


class EntityRelationship(BaseModel):
    source_id: str = Field(..., min_length=1)
    target_id: str = Field(..., min_length=1)
    relationship: str = Field(..., min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
