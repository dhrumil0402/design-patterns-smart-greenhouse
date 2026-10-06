from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import replace
from datetime import datetime

from domain.devices.entity import Device
from domain.sensors.ports import SensorPort

logger = logging.getLogger(__name__)


class SimulationSampler:
    """Records readings for tracked simulation sensors when their interval elapsed.

    run_once(now) takes the clock as an argument so tests never sleep.
    """

    def __init__(self, devices, readings, ingest, select_adapter: Callable[[Device], SensorPort]) -> None:
        self._devices = devices
        self._readings = readings
        self._ingest = ingest
        self._select_adapter = select_adapter

    def run_once(self, now: datetime) -> int:
        recorded = 0
        for device in self._devices.list_devices(role="sensor"):
            protocol = (device.default_config or {}).get("protocol")
            if protocol != "simulation" or not device.tracking_enabled:
                continue  # skips mqtt/other protocols and tracking-off devices
            last = self._readings.latest_recorded_at(device.id)
            if last is not None and (now - last).total_seconds() < device.sampling_interval_seconds:
                continue
            try:
                reading = self._select_adapter(device).read(device)
                # stamp with the sampler clock so the interval maths is consistent
                self._ingest.record(device.id, replace(reading, recorded_at=now))
                recorded += 1
            except Exception:
                logger.exception("sampler failed for device %s", device.id)
        return recorded
