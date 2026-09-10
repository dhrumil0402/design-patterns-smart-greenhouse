from __future__ import annotations

import uuid
from dataclasses import dataclass, field


@dataclass
class Sensor:
    """Plain domain entity for a greenhouse sensor. No ORM, no HTTP concerns."""

    device_type: str
    display_name: str
    default_config: dict = field(default_factory=dict)
    id: uuid.UUID | None = None
