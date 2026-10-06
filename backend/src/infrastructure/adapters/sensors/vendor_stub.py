from __future__ import annotations

import random
import time
from datetime import datetime, timezone

from domain.devices.entity import Device
from domain.sensors.ports import SensorPort
from domain.sensors.reading import Reading


class VendorProbeClient:
    """Adaptee: a stand-in for a vendor SDK we do not control.

    Its shape is deliberately different from our Reading:
      {"probe": "<id>", "data": {"v": <int>, "u": "pct_x100" | "lux_raw"}, "epoch": <int seconds>}
    """

    def poll(self, probe_id: str, device_type: str) -> dict:
        if device_type == "moisture_sensor":
            return {
                "probe": probe_id,
                "data": {"v": random.randint(2000, 6000), "u": "pct_x100"},
                "epoch": int(time.time()),
            }
        return {
            "probe": probe_id,
            "data": {"v": random.randint(200, 2000), "u": "lux_raw"},
            "epoch": int(time.time()),
        }


class VendorStubSensorAdapter(SensorPort):
    """Translates the vendor dict into a normalized Reading. Translation only."""

    def __init__(self, client: VendorProbeClient | None = None) -> None:
        self._client = client or VendorProbeClient()

    def read(self, device: Device) -> Reading:
        if device.id is None:
            raise ValueError("device must be persisted before it can be read")
        raw = self._client.poll(str(device.id), device.device_type)
        try:
            v = raw["data"]["v"]
            u = raw["data"]["u"]
            epoch = raw["epoch"]
        except (KeyError, TypeError) as exc:
            raise ValueError(f"malformed vendor payload: {exc}") from None

        if u == "pct_x100":      # 3120 -> 31.20 % -> 0.312 vwc
            value, unit = v / 10000, "vwc"
        elif u == "lux_raw":
            value, unit = float(v), "lux"
        else:
            raise ValueError(f"unknown vendor unit: {u!r}")

        return Reading(
            device_id=device.id,
            value=round(value, 4),
            unit=unit,
            source="vendor",
            recorded_at=datetime.fromtimestamp(epoch, tz=timezone.utc),
        )
