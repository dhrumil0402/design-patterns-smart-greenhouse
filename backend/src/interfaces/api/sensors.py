from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from application.sensors.service import SensorService
from infrastructure.db import get_db
from infrastructure.persistence.device_repository import DeviceRepository
from interfaces.api.schemas import SensorCreateRequest, SensorResponse

router = APIRouter(prefix="/api/sensors", tags=["sensors"])


def get_sensor_service(db: Session = Depends(get_db)) -> SensorService:
    return SensorService(DeviceRepository(db))


@router.post("", response_model=SensorResponse, status_code=201)
def create_sensor(
    payload: SensorCreateRequest,
    service: SensorService = Depends(get_sensor_service),
) -> SensorResponse:
    try:
        sensor = service.register_sensor(payload.type, payload.display_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    return SensorResponse.model_validate(sensor)


@router.get("", response_model=list[SensorResponse])
def list_sensors(service: SensorService = Depends(get_sensor_service)) -> list[SensorResponse]:
    sensors = service.list_sensors()
    return [SensorResponse.model_validate(s) for s in sensors]


