from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from sqlalchemy.orm import Session
from sqlalchemy.orm import Session

from domain.locations.entity import Location, LocationSummary, Zone
from domain.locations.entity import Location, LocationSummary, Zone
from domain.locations.entity import Location, Zone
from infrastructure.persistence.models import LocationRow, ZoneRow
from infrastructure.persistence.models import DeviceRow, LocationRow, ZoneRow


def _row_to_zone(row: ZoneRow) -> Zone:
    return Zone(
        id=row.id,
        name=row.name,
        moisture_threshold_low=float(row.moisture_threshold_low),
        moisture_threshold_high=float(row.moisture_threshold_high),
        schedule=row.schedule or {},
    )


def _row_to_location(row: LocationRow, zone_rows: list[ZoneRow]) -> Location:
    return Location(
        id=row.id,
        name=row.name,
        zones=tuple(_row_to_zone(z) for z in zone_rows),
    )


class LocationRepository:
    """Owns all SQL for `locations` and `zones`. Converts rows <-> Location/Zone."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def save_config(self, location: Location) -> Location:
        location_row = LocationRow(name=location.name)
        self._db.add(location_row)
        self._db.flush()  # assigns location_row.id via RETURNING, no commit yet

        zone_rows = [
            ZoneRow(
                location_id=location_row.id,
                name=zone.name,
                moisture_threshold_low=zone.moisture_threshold_low,
                moisture_threshold_high=zone.moisture_threshold_high,
                schedule=zone.schedule,
            )
            for zone in location.zones
        ]
        self._db.add_all(zone_rows)

        # One commit for both tables — a failure here rolls back the location too.
        self._db.commit()
        self._db.refresh(location_row)
        for row in zone_rows:
            self._db.refresh(row)

        return _row_to_location(location_row, zone_rows)

    def get_config(self, location_id: uuid.UUID) -> Location | None:
        location_row = self._db.get(LocationRow, location_id)
        if location_row is None:
            return None
        zone_rows = list(location_row.zones)
        return _row_to_location(location_row, zone_rows)

    def get_zone_location_id(self, zone_id: uuid.UUID) -> uuid.UUID | None:
        row = self._db.get(ZoneRow, zone_id)
        return row.location_id if row is not None else None
    def list_locations(self) -> list[LocationSummary]:
        # Documented order: newest first
        stmt = select(LocationRow).order_by(LocationRow.created_at.desc())
        rows = self._db.execute(stmt).scalars().all()
        return [LocationSummary(id=r.id, name=r.name) for r in rows]

    def delete_location(self, location_id: uuid.UUID) -> bool:
        row = self._db.get(LocationRow, location_id)
        if row is None:
            return False
        self._db.delete(row)  # zones are removed by the cascade
        self._db.commit()
        return True
    def location_exists(self, location_id: uuid.UUID) -> bool:
        return self._db.get(LocationRow, location_id) is not None

    def list_zones(self, location_id: uuid.UUID) -> list[Zone]:
        stmt = select(ZoneRow).where(ZoneRow.location_id == location_id).order_by(ZoneRow.name)
        return [_row_to_zone(r) for r in self._db.execute(stmt).scalars().all()]

    def add_zone(self, location_id: uuid.UUID, zone: Zone) -> Zone:
        row = ZoneRow(
            location_id=location_id,
            name=zone.name,
            moisture_threshold_low=zone.moisture_threshold_low,
            moisture_threshold_high=zone.moisture_threshold_high,
            schedule=zone.schedule,
        )
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return _row_to_zone(row)

    def update_zone(self, location_id: uuid.UUID, zone_id: uuid.UUID, zone: Zone) -> Zone | None:
        row = self._db.get(ZoneRow, zone_id)
        if row is None or row.location_id != location_id:
            return None
        row.name = zone.name
        row.moisture_threshold_low = zone.moisture_threshold_low
        row.moisture_threshold_high = zone.moisture_threshold_high
        row.schedule = zone.schedule
        self._db.commit()
        self._db.refresh(row)
        return _row_to_zone(row)

    def delete_zone(self, location_id: uuid.UUID, zone_id: uuid.UUID) -> bool:
        row = self._db.get(ZoneRow, zone_id)
        if row is None or row.location_id != location_id:
            return False
        # ON DELETE SET NULL would only clear devices.zone_id, so clear both ids here first.
        self._db.execute(
            update(DeviceRow)
            .where(DeviceRow.zone_id == zone_id)
            .values(zone_id=None, location_id=None)
        )
        self._db.delete(row)
        self._db.commit()  # one commit: devices and zone change together
        return True