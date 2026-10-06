from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from infrastructure.db import get_db
from infrastructure.persistence.device_repository import DeviceRepository

router = APIRouter(prefix="/api/devices", tags=["devices"])

MIN_INTERVAL_SECONDS = 5


class SamplingDto(BaseModel):
    sampling_interval_seconds: int
    tracking_enabled: bool


@router.get("/{device_id}/sampling", response_model=SamplingDto)
def get_sampling(device_id: uuid.UUID, db: Session = Depends(get_db)) -> SamplingDto:
    device = DeviceRepository(db).get_device(device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="device not found")
    return SamplingDto(
        sampling_interval_seconds=device.sampling_interval_seconds,
        tracking_enabled=device.tracking_enabled,
    )


@router.patch("/{device_id}/sampling", response_model=SamplingDto)
def update_sampling(device_id: uuid.UUID, body: SamplingDto, db: Session = Depends(get_db)) -> SamplingDto:
    if body.sampling_interval_seconds < MIN_INTERVAL_SECONDS:
        raise HTTPException(
            status_code=400,
            detail=f"sampling_interval_seconds must be at least {MIN_INTERVAL_SECONDS}",
        )
    device = DeviceRepository(db).update_sampling(
        device_id, body.sampling_interval_seconds, body.tracking_enabled
    )
    if device is None:
        raise HTTPException(status_code=404, detail="device not found")
    return body
