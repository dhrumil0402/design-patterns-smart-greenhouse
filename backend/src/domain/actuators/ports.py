from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID


class ActuatorPort(ABC):
    """Target interface for actuators. Phase 9 wraps this with decorators."""

    @abstractmethod
    def apply(self, device_id: UUID, command: str, payload: dict) -> None:
        """Apply a command (for example start_pump) to an actuator."""
        raise NotImplementedError
