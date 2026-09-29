from domain.locations.entity import Location, LocationConfig, Zone
from domain.locations.errors import ConfigurationError

MIN_THRESHOLD = 0.0
MAX_THRESHOLD = 1.0


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
            if not zone.name:
                raise ConfigurationError("zone name is required")
            if not (MIN_THRESHOLD <= zone.moisture_threshold_low <= MAX_THRESHOLD):
                raise ConfigurationError(
                    f"zone '{zone.name}' low threshold must be between "
                    f"{MIN_THRESHOLD} and {MAX_THRESHOLD}"
                )
            if not (MIN_THRESHOLD <= zone.moisture_threshold_high <= MAX_THRESHOLD):
                raise ConfigurationError(
                    f"zone '{zone.name}' high threshold must be between "
                    f"{MIN_THRESHOLD} and {MAX_THRESHOLD}"
                )
            if zone.moisture_threshold_low >= zone.moisture_threshold_high:
                raise ConfigurationError(
                    f"zone '{zone.name}' low threshold must be strictly less than high threshold"
                )

        return LocationConfig(location=Location(name=self._name, zones=tuple(self._zones)))