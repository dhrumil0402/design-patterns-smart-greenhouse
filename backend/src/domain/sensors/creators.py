from __future__ import annotations

from abc import ABC, abstractmethod

from domain.sensors.entity import Sensor


class SensorCreator(ABC):
    """Factory Method: subclasses decide the concrete sensor type and its defaults."""

    @abstractmethod
    def create_sensor(self, display_name: str | None = None) -> Sensor:
        raise NotImplementedError


class MoistureSensorCreator(SensorCreator):
    def create_sensor(self, display_name: str | None = None) -> Sensor:
        return Sensor(
            device_type="moisture_sensor",
            display_name=display_name or "Soil moisture sensor",
            default_config={
                "unit": "vwc",
                "sampling_interval_seconds": 300,
                "moisture_threshold_percent": 30,
            },
        )


class LightSensorCreator(SensorCreator):
    def create_sensor(self, display_name: str | None = None) -> Sensor:
        return Sensor(
            device_type="light_sensor",
            display_name=display_name or "Light sensor",
            default_config={
                "unit": "lux",
                "sampling_interval_seconds": 60,
            },
        )


_CREATORS: dict[str, SensorCreator] = {
    "moisture": MoistureSensorCreator(),
    "light": LightSensorCreator(),
}


def get_creator(sensor_type: str) -> SensorCreator:
    """Look up a creator by its short type key. Raises ValueError on an unknown type."""
    try:
        return _CREATORS[sensor_type]
    except KeyError:
        raise ValueError(f"Unknown sensor type: {sensor_type!r}") from None
