import uuid
from datetime import datetime

from sqlalchemy import Index, String, DateTime, func, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from infrastructure.persistence.base import Base

class DeviceRow(Base):
    __tablename__ = "devices"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    device_type: Mapped[str] = mapped_column(String(64), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="sensor", server_default="sensor", index=True)
    display_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    default_config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    device_family: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default="simulation"
    )

    __table_args__ = (
        Index("ix_devices_role", "role"),
        Index("ix_devices_family", "device_family"),
    )

# --- Phase 4: Location & Zone models ---

class LocationRow(Base):
    __tablename__ = "locations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    zones: Mapped[list["ZoneRow"]] = relationship(
        back_populates="location", cascade="all, delete-orphan"
    )


class ZoneRow(Base):
    __tablename__ = "zones"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    location_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    moisture_threshold_low: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    moisture_threshold_high: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    schedule: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")

    location: Mapped["LocationRow"] = relationship(back_populates="zones")

    __table_args__ = (
        Index("ix_zones_location_id", "location_id"),
    )