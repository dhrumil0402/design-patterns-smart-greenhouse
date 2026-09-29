from uuid import UUID

from pydantic import BaseModel, Field


class ZoneCreateDto(BaseModel):
    name: str
    moisture_threshold_low: float
    moisture_threshold_high: float
    schedule: dict = Field(default_factory=dict)


class LocationConfigCreateDto(BaseModel):
    location_name: str
    zones: list[ZoneCreateDto]


class ZoneReadDto(BaseModel):
    id: UUID
    location_id: UUID
    name: str
    moisture_threshold_low: float
    moisture_threshold_high: float
    schedule: dict


class LocationSummaryDto(BaseModel):
    id: UUID
    name: str


class LocationConfigReadDto(BaseModel):
    location: LocationSummaryDto
    zones: list[ZoneReadDto]