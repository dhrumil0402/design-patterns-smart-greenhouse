from __future__ import annotations

import logging
from uuid import UUID

from domain.actuators.ports import ActuatorPort

logger = logging.getLogger(__name__)


class SimulationActuatorAdapter(ActuatorPort):
    """Records intent in memory and logs it. No GPIO, no physical output."""

    def __init__(self) -> None:
        self.applied: list[tuple[UUID, str, dict]] = []

    def apply(self, device_id: UUID, command: str, payload: dict) -> None:
        self.applied.append((device_id, command, dict(payload)))
        logger.info("simulated actuator %s: %s %s", device_id, command, payload)
