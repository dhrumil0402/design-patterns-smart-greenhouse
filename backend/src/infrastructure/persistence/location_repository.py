from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from domain.locations.entity import Location, Zone
from infrastructure.persistence.models import LocationRow, ZoneRow


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