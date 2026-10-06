from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class Reading:
    """Normalized sensor reading. Every adapter must produce this exact shape."""

    device_id: UUID
    value: float
    unit: str
    source: str  # "simulation" | "mqtt" | "vendor"
    recorded_at: datetime  # timezone-aware

    def __post_init__(self) -> None:
        if self.recorded_at.tzinfo is None:
            raise ValueError("recorded_at must be timezone-aware")
