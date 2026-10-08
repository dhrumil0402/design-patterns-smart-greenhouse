import uuid

from application.locations.dto import ZoneCreateDto, ZoneReadDto, ZoneUpdateDto
from application.locations.errors import NotFoundError
from application.locations.mappers import zone_to_dto
from domain.locations.entity import Zone
from domain.locations.errors import ConfigurationError
from domain.locations.zone_rules import validate_unique_zone_names, validate_zone
from infrastructure.persistence.location_repository import LocationRepository


class ZoneManagementService:
    def __init__(self, repo: LocationRepository) -> None:
        self._repo = repo

    def _existing_zones(self, location_id: uuid.UUID) -> list[Zone]:
        if not self._repo.location_exists(location_id):
            raise NotFoundError("location not found")
        return self._repo.list_zones(location_id)

    def add_zone(self, location_id: uuid.UUID, request: ZoneCreateDto) -> ZoneReadDto:
        existing = self._existing_zones(location_id)
        zone = Zone(
            name=request.name.strip(),
            moisture_threshold_low=request.moisture_threshold_low,
            moisture_threshold_high=request.moisture_threshold_high,
            schedule=request.schedule,
        )
        validate_zone(zone)
        validate_unique_zone_names([*existing, zone])
        return zone_to_dto(location_id, self._repo.add_zone(location_id, zone))

    def update_zone(
        self, location_id: uuid.UUID, zone_id: uuid.UUID, request: ZoneUpdateDto
    ) -> ZoneReadDto:
        existing = self._existing_zones(location_id)
        current = next((z for z in existing if z.id == zone_id), None)
        if current is None:
            raise NotFoundError("zone not found in this location")
        updated = Zone(
            id=zone_id,
            name=request.name.strip(),
            moisture_threshold_low=request.moisture_threshold_low,
            moisture_threshold_high=request.moisture_threshold_high,
            schedule=request.schedule if request.schedule is not None else current.schedule,
        )
        validate_zone(updated)
        others = [z for z in existing if z.id != zone_id]
        validate_unique_zone_names([*others, updated])
        saved = self._repo.update_zone(location_id, zone_id, updated)
        return zone_to_dto(location_id, saved)

    def delete_zone(self, location_id: uuid.UUID, zone_id: uuid.UUID) -> None:
        existing = self._existing_zones(location_id)
        if not any(z.id == zone_id for z in existing):
            raise NotFoundError("zone not found in this location")
        if len(existing) <= 1:
            raise ConfigurationError("a location must keep at least one zone")
        self._repo.delete_zone(location_id, zone_id)