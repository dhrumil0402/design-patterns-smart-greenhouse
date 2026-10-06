from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from domain.sensors.reading import Reading
from infrastructure.persistence.models import ReadingRow


def _row_to_reading(row: ReadingRow) -> Reading:
    return Reading(
        device_id=row.device_id,
        value=float(row.value),
        unit=row.unit,
        source=row.source,
        recorded_at=row.recorded_at,
    )


class ReadingRepository:
    """Owns all SQL for `sensor_readings`. History is append-only."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def insert(self, reading: Reading) -> Reading:
        row = ReadingRow(
            device_id=reading.device_id,
            value=reading.value,
            unit=reading.unit,
            source=reading.source,
            recorded_at=reading.recorded_at,
        )
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return _row_to_reading(row)

    def list_for_device(self, device_id: uuid.UUID, limit: int = 20) -> list[Reading]:
        stmt = (
            select(ReadingRow)
            .where(ReadingRow.device_id == device_id)
            .order_by(ReadingRow.recorded_at.desc())
            .limit(limit)
        )
        return [_row_to_reading(r) for r in self._db.execute(stmt).scalars().all()]

    def latest_recorded_at(self, device_id: uuid.UUID) -> datetime | None:
        stmt = select(func.max(ReadingRow.recorded_at)).where(ReadingRow.device_id == device_id)
        return self._db.execute(stmt).scalar()
