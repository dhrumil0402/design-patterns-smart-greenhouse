from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.sensors.entity import Sensor
from domain.devices.entity import Device
from infrastructure.persistence.models import DeviceRow


def _row_to_sensor(row: DeviceRow) -> Sensor:
    return Sensor(
        id=row.id,
        device_type=row.device_type,
        display_name=row.display_name or row.device_type,
        default_config=row.default_config or {},
    )


def _row_to_device(row: DeviceRow) -> Device:
    return Device(
        id=row.id,
        device_type=row.device_type,
        role=row.role,
        device_family=row.device_family,
        display_name=row.display_name or row.device_type,
        default_config=row.default_config or {},
        sampling_interval_seconds=row.sampling_interval_seconds,
        tracking_enabled=row.tracking_enabled,
    )


class DeviceRepository:
    """Owns all SQL for the `devices` table. Converts DeviceRow <-> Sensor/Device."""

    def __init__(self, db: Session) -> None:
        self._db = db

    # --- Phase 2 (Factory Method) methods ---

    def add(self, sensor: Sensor) -> Sensor:
        row = DeviceRow(
            device_type=sensor.device_type,
            role="sensor",
            display_name=sensor.display_name,
            default_config=sensor.default_config,
            sampling_interval_seconds=max(
                5, int(sensor.default_config.get("sampling_interval_seconds", 300))
            ),
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

    # --- Phase 3 (Abstract Factory) additions ---

    def save_device(self, device: Device) -> Device:
        row = DeviceRow(
            device_type=device.device_type,
            role=device.role,
            device_family=device.device_family,
            display_name=device.display_name,
            default_config=device.default_config,
            sampling_interval_seconds=device.sampling_interval_seconds,
            tracking_enabled=device.tracking_enabled,
        )
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return _row_to_device(row)

    def save_devices(self, devices: list[Device]) -> list[Device]:
        return [self.save_device(d) for d in devices]

    def list_devices(
        self, *, device_family: str | None = None, role: str | None = None
    ) -> list[Device]:
        stmt = select(DeviceRow)
        if device_family:
            stmt = stmt.where(DeviceRow.device_family == device_family)
        if role:
            stmt = stmt.where(DeviceRow.role == role)
        stmt = stmt.order_by(DeviceRow.created_at.desc())
        rows = self._db.execute(stmt).scalars().all()
        return [_row_to_device(r) for r in rows]
    def get_device(self, device_id: uuid.UUID) -> Device | None:
        row = self._db.get(DeviceRow, device_id)
        return _row_to_device(row) if row is not None else None

    def update_sampling(self, device_id: uuid.UUID, interval: int, tracking: bool) -> Device | None:
        row = self._db.get(DeviceRow, device_id)
        if row is None:
            return None
        row.sampling_interval_seconds = interval
        row.tracking_enabled = tracking
        self._db.commit()
        self._db.refresh(row)
        return _row_to_device(row)
