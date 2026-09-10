from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class SensorCreateRequest(BaseModel):
    type: str = Field(..., examples=["moisture", "light"])
    display_name: str | None = None


class SensorResponse(BaseModel):
    id: uuid.UUID
    device_type: str
    display_name: str
    default_config: dict

    model_config = {"from_attributes": True}
