from __future__ import annotations

import math
from datetime import datetime, timezone

from domain.devices.entity import Device
from domain.sensors.reading import Reading


class MqttSensorAdapter:
    """Translates an inbound MQTT payload dict into a Reading.

    Payload shape: {"value": 0.41, "unit": "vwc"}
    No broker connection here. Phase 12 delivers payloads; this phase only translates.
    """

    def translate(self, device: Device, payload: dict) -> Reading:
        if device.id is None:
            raise ValueError("device must be persisted before it can be read")
        value = payload.get("value")
        unit = payload.get("unit")
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError("payload 'value' must be a finite number")
        if not isinstance(unit, str) or not unit.strip():
            raise ValueError("payload 'unit' must be a non-empty string")
        return Reading(
            device_id=device.id,
            value=float(value),
            unit=unit.strip(),
            source="mqtt",
            recorded_at=datetime.now(timezone.utc),
        )
