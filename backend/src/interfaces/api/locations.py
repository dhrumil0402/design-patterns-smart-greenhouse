import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from infrastructure.db import get_db
from infrastructure.persistence.location_repository import LocationRepository
from application.locations.config_service import LocationConfigService
from application.locations.dto import LocationConfigCreateDto, LocationConfigReadDto
from application.locations.dto import (
    LocationConfigCreateDto,
    LocationConfigReadDto,
    LocationSummaryDto,
)
from application.locations.dto import (
    LocationConfigCreateDto,
    LocationConfigReadDto,
    LocationSummaryDto,
    ZoneCreateDto,
    ZoneReadDto,
    ZoneUpdateDto,
)
from application.locations.errors import NotFoundError
from application.locations.zone_service import ZoneManagementService
from infrastructure.persistence.device_repository import DeviceRepository
from application.devices.dto import DeviceDto
from application.devices.errors import AssignmentNotFoundError
from application.devices.mappers import devices_to_dtos
from application.devices.zone_assignment_service import ZoneAssignmentService


router = APIRouter(prefix="/api/locations", tags=["locations"])


def get_service(db: Session = Depends(get_db)) -> LocationConfigService:
    return LocationConfigService(LocationRepository(db))

def get_assignment_service(db: Session = Depends(get_db)) -> ZoneAssignmentService:
    return ZoneAssignmentService(DeviceRepository(db), LocationRepository(db))

@router.post("/config", response_model=LocationConfigReadDto, status_code=201)
def create_location_config(
    request: LocationConfigCreateDto,
    service: LocationConfigService = Depends(get_service),
):
    try:
        return service.build_and_save(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/{location_id}/config", response_model=LocationConfigReadDto)
def get_location_config(
    location_id: uuid.UUID,
    service: LocationConfigService = Depends(get_service),
):
    result = service.get_config(location_id)
    if result is None:
        raise HTTPException(status_code=404, detail="location not found")
    return result
def get_zone_service(db: Session = Depends(get_db)) -> ZoneManagementService:
    return ZoneManagementService(LocationRepository(db))

@router.get("/{location_id}/zones/{zone_id}/devices", response_model=list[DeviceDto])
def list_zone_devices(
    location_id: uuid.UUID,
    zone_id: uuid.UUID,
    service: ZoneAssignmentService = Depends(get_assignment_service),
):
    try:
        devices = service.list_devices(location_id, zone_id)
    except AssignmentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return devices_to_dtos(devices)

@router.get("", response_model=list[LocationSummaryDto])
def list_locations(service: LocationConfigService = Depends(get_service)):
    return service.list_locations()


@router.delete("/{location_id}", status_code=204)
def delete_location(
    location_id: uuid.UUID,
    service: LocationConfigService = Depends(get_service),
):
    if not service.delete_location(location_id):
        raise HTTPException(status_code=404, detail="location not found")
    return Response(status_code=204)
@router.post("/{location_id}/zones", response_model=ZoneReadDto, status_code=201)
def add_zone(
    location_id: uuid.UUID,
    request: ZoneCreateDto,
    service: ZoneManagementService = Depends(get_zone_service),
):
    try:
        return service.add_zone(location_id, request)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.patch("/{location_id}/zones/{zone_id}", response_model=ZoneReadDto)
def update_zone(
    location_id: uuid.UUID,
    zone_id: uuid.UUID,
    request: ZoneUpdateDto,
    service: ZoneManagementService = Depends(get_zone_service),
):
    try:
        return service.update_zone(location_id, zone_id, request)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/{location_id}/zones/{zone_id}", status_code=204)
def delete_zone(
    location_id: uuid.UUID,
    zone_id: uuid.UUID,
    service: ZoneManagementService = Depends(get_zone_service),
):
    try:
        service.delete_zone(location_id, zone_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return Response(status_code=204)