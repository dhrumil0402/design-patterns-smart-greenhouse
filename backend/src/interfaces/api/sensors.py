from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from application.readings.dto import ReadingDto
from application.readings.service import DeviceNotFoundError, ReadingIngest
from application.sensors.service import SensorService
from infrastructure.adapters.selector import select_sensor_adapter
from infrastructure.db import get_db
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.persistence.reading_repository import ReadingRepository
from interfaces.api.schemas import SensorCreateRequest, SensorResponse

router = APIRouter(prefix="/api/sensors", tags=["sensors"])


def get_sensor_service(db: Session = Depends(get_db)) -> SensorService:
    return SensorService(DeviceRepository(db))


def get_ingest(db: Session = Depends(get_db)) -> ReadingIngest:
    return ReadingIngest(DeviceRepository(db), ReadingRepository(db), select_sensor_adapter)


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


@router.post("/{sensor_id}/read", response_model=ReadingDto, status_code=201)
def read_sensor(sensor_id: uuid.UUID, ingest: ReadingIngest = Depends(get_ingest)) -> ReadingDto:
    try:
        return ingest.take_reading(sensor_id)
    except DeviceNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None


@router.get("/{sensor_id}/readings", response_model=list[ReadingDto])
def list_readings(
    sensor_id: uuid.UUID,
    limit: int = Query(20, ge=1, le=500),
    ingest: ReadingIngest = Depends(get_ingest),
) -> list[ReadingDto]:
    try:
        return ingest.list_readings(sensor_id, limit)
    except DeviceNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
