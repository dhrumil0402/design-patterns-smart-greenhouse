from domain.locations.config_builder import LocationConfigBuilder
from domain.locations.entity import Location, LocationConfig
from application.locations.dto import (
    LocationConfigCreateDto,
    LocationConfigReadDto,
    LocationSummaryDto,
    ZoneReadDto,
)


def request_to_config(dto: LocationConfigCreateDto) -> LocationConfig:
    builder = LocationConfigBuilder().with_location_name(dto.location_name)
    for zone in dto.zones:
        builder.add_zone(
            name=zone.name,
            moisture_threshold_low=zone.moisture_threshold_low,
            moisture_threshold_high=zone.moisture_threshold_high,
            schedule=zone.schedule,
        )
    return builder.build()  # raises ConfigurationError before any persistence


def location_to_dto(location: Location) -> LocationConfigReadDto:
    return LocationConfigReadDto(
        location=LocationSummaryDto(id=location.id, name=location.name),
        zones=[
            ZoneReadDto(
                id=zone.id,
                location_id=location.id,
                name=zone.name,
                moisture_threshold_low=zone.moisture_threshold_low,
                moisture_threshold_high=zone.moisture_threshold_high,
                schedule=zone.schedule,
            )
            for zone in location.zones
        ],
    )