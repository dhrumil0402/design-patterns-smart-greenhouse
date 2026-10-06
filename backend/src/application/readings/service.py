from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from application.readings.dto import ReadingDto, reading_to_dto
from domain.devices.entity import Device
from domain.sensors.ports import SensorPort
from domain.sensors.reading import Reading


class DeviceNotFoundError(LookupError):
    """The API maps this to 404."""


class ReadingIngest:
    """The ONLY writer of sensor_readings.

    Manual read, the simulation sampler, and (Phase 12) device HTTP / MQTT all
    funnel through here. The adapter selector is injected so this class never
    imports concrete adapters.
    """

    def __init__(self, devices, readings, select_adapter: Callable[[Device], SensorPort]) -> None:
        self._devices = devices
        self._readings = readings
        self._select_adapter = select_adapter

    def _sensor(self, device_id: UUID) -> Device:
        device = self._devices.get_device(device_id)
        if device is None:
            raise DeviceNotFoundError(f"device {device_id} not found")
        if device.role != "sensor":
            raise ValueError("only sensors can produce readings")
        return device

    def take_reading(self, device_id: UUID) -> ReadingDto:
        """One-shot read: adapter -> persist -> DTO."""
        device = self._sensor(device_id)
        reading = self._select_adapter(device).read(device)
        return reading_to_dto(self._readings.insert(reading))

    def record(self, device_id: UUID, reading: Reading) -> ReadingDto:
        """Persist an already translated reading (sampler, MQTT, device HTTP)."""
        self._sensor(device_id)
        if reading.device_id != device_id:
            raise ValueError("reading.device_id does not match device_id")
        return reading_to_dto(self._readings.insert(reading))

    def list_readings(self, device_id: UUID, limit: int = 20) -> list[ReadingDto]:
        self._sensor(device_id)
        return [reading_to_dto(r) for r in self._readings.list_for_device(device_id, limit)]
