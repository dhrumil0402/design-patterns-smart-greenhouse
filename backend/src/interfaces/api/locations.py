import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from infrastructure.db import get_db
from infrastructure.persistence.location_repository import LocationRepository
from application.locations.config_service import LocationConfigService
from application.locations.dto import LocationConfigCreateDto, LocationConfigReadDto

router = APIRouter(prefix="/api/locations", tags=["locations"])


def get_service(db: Session = Depends(get_db)) -> LocationConfigService:
    return LocationConfigService(LocationRepository(db))


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
