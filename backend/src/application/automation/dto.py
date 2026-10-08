from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class StrategySaveDto(BaseModel):
    """Request body for PUT /api/locations/{location_id}/automation."""

    strategy_key: str


class StrategyReadDto(BaseModel):
    location_id: UUID
    strategy_key: str


class RecommendationDto(BaseModel):
    """Evaluate response: one action and reason for the whole location."""

    location_id: UUID
    strategy_key: str
    action: str
    reason: str
