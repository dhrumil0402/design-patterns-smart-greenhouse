import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from application.locations.errors import NotFoundError
from application.overview.dto import LocationOverviewDto
from application.overview.facade import LocationOverviewFacade
from infrastructure.db import get_db
from infrastructure.overview_factory import build_location_overview_facade

router = APIRouter(prefix="/api/locations", tags=["overview"])


def get_facade(db: Session = Depends(get_db)) -> LocationOverviewFacade:
    return build_location_overview_facade(db)


@router.get("/{location_id}/overview", response_model=LocationOverviewDto)
def get_location_overview(
    location_id: uuid.UUID,
    facade: LocationOverviewFacade = Depends(get_facade),
):
    try:
        return facade.get_overview(location_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
