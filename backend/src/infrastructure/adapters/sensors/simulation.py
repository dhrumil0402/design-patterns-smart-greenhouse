from __future__ import annotations

import random
from datetime import datetime, timezone

from domain.devices.entity import Device
from domain.sensors.ports import SensorPort
from domain.sensors.reading import Reading

# Documented ranges per device type: (low, high, unit)
_RANGES: dict[str, tuple[float, float, str]] = {
    "moisture_sensor": (0.2, 0.6, "vwc"),
    "light_sensor": (200.0, 2000.0, "lux"),
}


class SimulationSensorAdapter(SensorPort):
    """Generates a plausible value in code. No hardware, no network."""

    def __init__(self, rng: random.Random | None = None) -> None:
        self._rng = rng or random.Random()

    def read(self, device: Device) -> Reading:
        if device.id is None:
            raise ValueError("device must be persisted before it can be read")
        try:
            low, high, unit = _RANGES[device.device_type]
        except KeyError:
            raise ValueError(f"no simulation range for device type {device.device_type!r}") from None
        return Reading(
            device_id=device.id,
            value=round(self._rng.uniform(low, high), 4),
            unit=unit,
            source="simulation",
            recorded_at=datetime.now(timezone.utc),
        )
