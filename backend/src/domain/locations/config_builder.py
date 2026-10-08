from domain.locations.entity import Location, LocationConfig, Zone
from domain.locations.errors import ConfigurationError
from domain.locations.zone_rules import validate_unique_zone_names, validate_zone


class LocationConfigBuilder:
    def __init__(self) -> None:
        self._name: str | None = None
        self._zones: list[Zone] = []

    def with_location_name(self, name: str) -> "LocationConfigBuilder":
        self._name = name.strip() if name else name
        return self

    def add_zone(
        self,
        name: str,
        moisture_threshold_low: float,
        moisture_threshold_high: float,
        schedule: dict | None = None,
    ) -> "LocationConfigBuilder":
        self._zones.append(
            Zone(
                name=name,
                moisture_threshold_low=moisture_threshold_low,
                moisture_threshold_high=moisture_threshold_high,
                schedule=schedule or {},
            )
        )
        return self

    def build(self) -> LocationConfig:
        if not self._name:
            raise ConfigurationError("location name is required")
        if not self._zones:
            raise ConfigurationError("at least one zone is required")

        for zone in self._zones:
            validate_zone(zone)
        validate_unique_zone_names(self._zones)

        return LocationConfig(location=Location(name=self._name, zones=tuple(self._zones)))