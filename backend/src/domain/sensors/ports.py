from __future__ import annotations

from abc import ABC, abstractmethod

from domain.devices.entity import Device
from domain.sensors.reading import Reading


class SensorPort(ABC):
    """Target interface (Adapter pattern). Application code depends only on this."""

    @abstractmethod
    def read(self, device: Device) -> Reading:
        """Return one normalized reading for the given sensor device."""
        raise NotImplementedError
