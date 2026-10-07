from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class LocationAutomationContext:
    """Everything a strategy may look at for ONE zone. Plain values only."""

    location_id: UUID
    zone_id: UUID
    moisture: float | None      # latest moisture from sensors in this zone; None = no sensor
    moisture_low: float         # zone's low threshold (from zones table)
    moisture_high: float        # zone's high threshold
    light: float | None = None  # optional, unused by the two moisture strategies
