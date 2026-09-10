from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.sensors.entity import Sensor
from infrastructure.persistence.models import DeviceRow


def _row_to_sensor(row: DeviceRow) -> Sensor:
    return Sensor(
        id=row.id,
        device_type=row.device_type,
        display_name=row.display_name or row.device_type,
        default_config=row.default_config or {},
    )


class DeviceRepository:
    """Owns all SQL for the `devices` table. Converts DeviceRow <-> Sensor."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def add(self, sensor: Sensor) -> Sensor:
        row = DeviceRow(
            device_type=sensor.device_type,
            role="sensor",
            display_name=sensor.display_name,
            default_config=sensor.default_config,
        )
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return _row_to_sensor(row)

    def list_sensors(self) -> list[Sensor]:
        stmt = select(DeviceRow).where(DeviceRow.role == "sensor").order_by(DeviceRow.created_at)
        rows = self._db.execute(stmt).scalars().all()
        return [_row_to_sensor(row) for row in rows]

    def get_by_id(self, sensor_id: uuid.UUID) -> Sensor | None:
        row = self._db.get(DeviceRow, sensor_id)
        if row is None or row.role != "sensor":
            return None
        return _row_to_sensor(row)
