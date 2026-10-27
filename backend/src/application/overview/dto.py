from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class OverviewLocationDto(BaseModel):
    id: UUID
    name: str


class DeviceCountsDto(BaseModel):
    """Counts of ASSIGNED devices only (this location_id and a non-null zone_id)."""

    sensor: int
    actuator: int


class OverviewDeviceDto(BaseModel):
    id: UUID
    device_type: str
    role: str
    display_name: str


class OverviewReadingDto(BaseModel):
    """Newest sensor_readings row for one device. Tracking and interval are copied from the device."""

    device_id: UUID
    value: float
    unit: str
    recorded_at: datetime
    tracking_enabled: bool
    sampling_interval_seconds: int


class OverviewZoneDto(BaseModel):
    id: UUID
    name: str
    moisture_threshold_low: float
    moisture_threshold_high: float
    devices: list[OverviewDeviceDto]
    latest_readings: list[OverviewReadingDto]  # devices with no reading are left out


class OverviewRecommendationDto(BaseModel):
    action: str
    reason: str


class LocationOverviewDto(BaseModel):
    """Read model for GET /api/locations/{location_id}/overview."""

    location: OverviewLocationDto
    device_counts: DeviceCountsDto
    zones: list[OverviewZoneDto]  # every zone on the location, including empty ones
    strategy_key: str | None
    last_recommendation: OverviewRecommendationDto | None  # null when no key is saved
