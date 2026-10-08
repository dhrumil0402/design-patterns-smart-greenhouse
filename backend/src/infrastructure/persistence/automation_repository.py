from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from infrastructure.persistence.models import AutomationRuleRow, DeviceRow, ReadingRow


class AutomationRepository:
    """SQL for `automation_rules` (one strategy per location) and the per-zone moisture lookup."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_strategy_key(self, location_id: uuid.UUID) -> str | None:
        stmt = select(AutomationRuleRow.strategy_key).where(
            AutomationRuleRow.location_id == location_id
        )
        return self._db.execute(stmt).scalar_one_or_none()

    def upsert_strategy_key(self, location_id: uuid.UUID, strategy_key: str) -> None:
        """Insert the rule, or update it if this location already has one."""
        stmt = insert(AutomationRuleRow).values(
            location_id=location_id, strategy_key=strategy_key
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["location_id"],
            set_={"strategy_key": strategy_key, "updated_at": func.now()},
        )
        self._db.execute(stmt)
        self._db.commit()

    def latest_moisture_by_zone(self, zone_ids: list[uuid.UUID]) -> dict[uuid.UUID, float]:
        """Latest moisture value per zone, from moisture sensors assigned to that zone.

        A zone with no assigned moisture sensor, or no reading yet, is simply absent.
        Unassigned devices (zone_id NULL) can never match, so they are never used.
        """
        if not zone_ids:
            return {}
        stmt = (
            select(DeviceRow.zone_id, ReadingRow.value)
            .select_from(DeviceRow)
            .join(ReadingRow, ReadingRow.device_id == DeviceRow.id)
            .where(
                DeviceRow.zone_id.in_(zone_ids),
                DeviceRow.role == "sensor",
                DeviceRow.device_type == "moisture_sensor",
            )
            .distinct(DeviceRow.zone_id)  # PostgreSQL DISTINCT ON: one row per zone
            .order_by(DeviceRow.zone_id, ReadingRow.recorded_at.desc())  # newest reading wins
        )
        return {zone_id: float(value) for zone_id, value in self._db.execute(stmt).all()}
