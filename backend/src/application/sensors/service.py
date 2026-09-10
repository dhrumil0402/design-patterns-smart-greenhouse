from __future__ import annotations

import uuid

from domain.sensors.creators import get_creator
from domain.sensors.entity import Sensor
from infrastructure.persistence.device_repository import DeviceRepository


class SensorService:
    """Use-case layer: orchestrates Factory Method creation + persistence.

    No SQL and no HTTP here — just the business steps.
    """

    def __init__(self, repository: DeviceRepository) -> None:
        self._repository = repository

    def register_sensor(self, sensor_type: str, display_name: str | None = None) -> Sensor:
        creator = get_creator(sensor_type)
        sensor = creator.create_sensor(display_name=display_name)
        return self._repository.add(sensor)

    def list_sensors(self) -> list[Sensor]:
        return self._repository.list_sensors()

    def get_sensor(self, sensor_id: uuid.UUID) -> Sensor | None:
        return self._repository.get_by_id(sensor_id)

