import uuid

from application.locations.dto import LocationConfigCreateDto, LocationConfigReadDto
from application.locations.mappers import location_to_dto, request_to_config
from infrastructure.persistence.location_repository import LocationRepository


class LocationConfigService:
    def __init__(self, repo: LocationRepository) -> None:
        self._repo = repo

    def build_and_save(self, request: LocationConfigCreateDto) -> LocationConfigReadDto:
        config = request_to_config(request)  # raises ConfigurationError if invalid
        saved = self._repo.save_config(config.location)
        return location_to_dto(saved)

    def get_config(self, location_id: uuid.UUID) -> LocationConfigReadDto | None:
        location = self._repo.get_config(location_id)
        if location is None:
            return None
        return location_to_dto(location)