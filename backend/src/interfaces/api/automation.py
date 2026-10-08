import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from application.automation.dto import RecommendationDto, StrategyReadDto, StrategySaveDto
from application.automation.service import AutomationService
from application.locations.errors import NotFoundError
from infrastructure.db import get_db
from infrastructure.persistence.automation_repository import AutomationRepository
from infrastructure.persistence.location_repository import LocationRepository

router = APIRouter(prefix="/api/locations", tags=["automation"])


def get_service(db: Session = Depends(get_db)) -> AutomationService:
    return AutomationService(LocationRepository(db), AutomationRepository(db))


@router.put("/{location_id}/automation", response_model=StrategyReadDto)
def save_strategy(
    location_id: uuid.UUID,
    request: StrategySaveDto,
    service: AutomationService = Depends(get_service),
):
    try:
        return service.set_strategy(location_id, request.strategy_key)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{location_id}/automation/evaluate", response_model=RecommendationDto)
def evaluate_automation(
    location_id: uuid.UUID,
    service: AutomationService = Depends(get_service),
):
    try:
        return service.evaluate(location_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
