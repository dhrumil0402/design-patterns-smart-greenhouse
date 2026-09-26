from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from infrastructure.db import get_db
from infrastructure.persistence.device_repository import DeviceRepository
from application.devices.family_service import DeviceFamilyService
from application.devices.mappers import devices_to_dtos
from application.devices.dto import DeviceDto

router = APIRouter(prefix="/api/devices", tags=["devices"])


def get_service(db: Session = Depends(get_db)) -> DeviceFamilyService:
    return DeviceFamilyService(DeviceRepository(db))


@router.get("", response_model=list[DeviceDto])
def list_devices(
    family: str | None = None,
    role: str | None = None,
    service: DeviceFamilyService = Depends(get_service),
):
    devices = service.list_devices(device_family=family, role=role)
    return devices_to_dtos(devices)


@router.post("/provision", response_model=list[DeviceDto], status_code=201)
def provision_family(
    family: str,
    service: DeviceFamilyService = Depends(get_service),
):
    try:
        devices = service.provision_family(family)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return devices_to_dtos(devices)