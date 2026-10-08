from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from infrastructure.db import get_db
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.persistence.location_repository import LocationRepository
from application.devices.family_service import DeviceFamilyService
from application.devices.zone_assignment_service import ZoneAssignmentService
from application.devices.errors import AssignmentNotFoundError
from application.devices.mappers import device_to_dto, devices_to_dtos
from application.devices.dto import DeviceDto, ZoneAssignmentRequestDto

router = APIRouter(prefix="/api/devices", tags=["devices"])


def get_service(db: Session = Depends(get_db)) -> DeviceFamilyService:
    return DeviceFamilyService(DeviceRepository(db))

def get_assignment_service(db: Session = Depends(get_db)) -> ZoneAssignmentService:
    return ZoneAssignmentService(DeviceRepository(db), LocationRepository(db))

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

@router.patch("/{device_id}/zone", response_model=DeviceDto)
def assign_device_zone(
    device_id: UUID,
    body: ZoneAssignmentRequestDto,
    service: ZoneAssignmentService = Depends(get_assignment_service),
):
    try:
        device = service.assign(device_id, body.zone_id)
    except AssignmentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return device_to_dto(device)