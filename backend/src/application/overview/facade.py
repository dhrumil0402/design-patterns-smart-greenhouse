from __future__ import annotations

from uuid import UUID

from application.locations.errors import NotFoundError
from application.overview.dto import (
    DeviceCountsDto,
    LocationOverviewDto,
    OverviewDeviceDto,
    OverviewLocationDto,
    OverviewReadingDto,
    OverviewRecommendationDto,
    OverviewZoneDto,
)


class LocationOverviewFacade:
    """One entry point for the dashboard overview.

    It only coordinates existing subsystems (locations, assigned devices, readings, saved strategy,
    automation evaluate). It owns no SQL and no irrigation policy.
    """

    def __init__(self, locations, devices, readings, rules, automation) -> None:
        self._locations = locations    # LocationRepository: get_config
        self._devices = devices        # DeviceRepository: list_assigned_devices
        self._readings = readings      # ReadingRepository: latest_for_devices
        self._rules = rules            # AutomationRepository: get_strategy_key
        self._automation = automation  # AutomationService: evaluate (calls decide)

    def get_overview(self, location_id: UUID) -> LocationOverviewDto:
        # 1. Location and every zone (one load).
        location = self._locations.get_config(location_id)
        if location is None:
            raise NotFoundError("location not found")

        # 2. Assigned devices for the whole location (one query).
        devices = self._devices.list_assigned_devices(location_id)

        # 3. Newest reading for all of those devices (one query, not one per device).
        latest = self._readings.latest_for_devices([device.id for device in devices])

        zones = []
        for zone in sorted(location.zones, key=lambda z: z.name):
            in_zone = [device for device in devices if device.zone_id == zone.id]
            zones.append(
                OverviewZoneDto(
                    id=zone.id,
                    name=zone.name,
                    moisture_threshold_low=zone.moisture_threshold_low,
                    moisture_threshold_high=zone.moisture_threshold_high,
                    devices=[
                        OverviewDeviceDto(
                            id=device.id,
                            device_type=device.device_type,
                            role=device.role,
                            display_name=device.display_name,
                        )
                        for device in in_zone
                    ],
                    latest_readings=[
                        OverviewReadingDto(
                            device_id=device.id,
                            value=latest[device.id].value,
                            unit=latest[device.id].unit,
                            recorded_at=latest[device.id].recorded_at,
                            tracking_enabled=device.tracking_enabled,
                            sampling_interval_seconds=device.sampling_interval_seconds,
                        )
                        for device in in_zone
                        if device.id in latest
                    ],
                )
            )

        # 4. Saved strategy key; 5. evaluate only when one exists. Computed per request, never stored.
        strategy_key = self._rules.get_strategy_key(location_id)
        recommendation = None
        if strategy_key is not None:
            result = self._automation.evaluate(location_id)
            recommendation = OverviewRecommendationDto(action=result.action, reason=result.reason)

        return LocationOverviewDto(
            location=OverviewLocationDto(id=location.id, name=location.name),
            device_counts=DeviceCountsDto(
                sensor=sum(1 for device in devices if device.role == "sensor"),
                actuator=sum(1 for device in devices if device.role == "actuator"),
            ),
            zones=zones,
            strategy_key=strategy_key,
            last_recommendation=recommendation,
        )
