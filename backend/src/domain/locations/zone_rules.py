from domain.locations.entity import Zone
from domain.locations.errors import ConfigurationError

MIN_THRESHOLD = 0.0
MAX_THRESHOLD = 1.0


def normalize_zone_name(name: str) -> str:
    return name.strip().casefold()


def validate_zone(zone: Zone) -> None:
    if not zone.name or not zone.name.strip():
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


def validate_unique_zone_names(zones) -> None:
    seen: set[str] = set()
    for zone in zones:
        key = normalize_zone_name(zone.name)
        if key in seen:
            raise ConfigurationError(
                f"zone name '{zone.name}' is used more than once in this location"
            )
        seen.add(key)