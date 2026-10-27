from __future__ import annotations

from sqlalchemy.orm import Session

from application.automation.service import AutomationService
from application.overview.facade import LocationOverviewFacade
from infrastructure.persistence.automation_repository import AutomationRepository
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.persistence.location_repository import LocationRepository
from infrastructure.persistence.reading_repository import ReadingRepository


def build_location_overview_facade(db: Session) -> LocationOverviewFacade:
    """Wires the facade's collaborators so the overview router never imports a repository."""
    locations = LocationRepository(db)
    rules = AutomationRepository(db)
    return LocationOverviewFacade(
        locations=locations,
        devices=DeviceRepository(db),
        readings=ReadingRepository(db),
        rules=rules,
        automation=AutomationService(locations, rules),
    )
