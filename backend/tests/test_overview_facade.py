from datetime import datetime, timezone
from uuid import uuid4

import pytest

from application.automation.dto import RecommendationDto
from application.locations.errors import NotFoundError
from application.overview.facade import LocationOverviewFacade
from domain.devices.entity import Device
from domain.locations.entity import Location, Zone
from domain.sensors.reading import Reading

LOCATION_ID = uuid4()
ZONE = Zone(id=uuid4(), name="Bench 1", moisture_threshold_low=0.2,
            moisture_threshold_high=0.45, schedule={})
SENSOR = Device(id=uuid4(), device_type="moisture_sensor", role="sensor",
                device_family="simulation", display_name="Bench moisture", default_config={},
                sampling_interval_seconds=120, tracking_enabled=True,
                zone_id=ZONE.id, location_id=LOCATION_ID)


class FakeLocations:
    def get_config(self, location_id):
        if location_id != LOCATION_ID:
            return None
        return Location(id=LOCATION_ID, name="Lab Site A", zones=(ZONE,))


class FakeDevices:
    def list_assigned_devices(self, location_id):
        return [SENSOR] if location_id == LOCATION_ID else []


class FakeReadings:
    def __init__(self):
        self.calls = []

    def latest_for_devices(self, device_ids):
        self.calls.append(device_ids)
        return {SENSOR.id: Reading(device_id=SENSOR.id, value=0.31, unit="vwc",
                                   source="mqtt", recorded_at=datetime.now(timezone.utc))}


class FakeRules:
    def __init__(self, key=None):
        self.key = key

    def get_strategy_key(self, location_id):
        return self.key


class FakeAutomation:
    def __init__(self):
        self.calls = 0

    def evaluate(self, location_id):
        self.calls += 1
        return RecommendationDto(location_id=location_id, strategy_key="conservative",
                                 action="wait", reason="Bench 1: ok")


def make(key=None):
    readings, automation = FakeReadings(), FakeAutomation()
    facade = LocationOverviewFacade(FakeLocations(), FakeDevices(), readings, FakeRules(key),
                                    automation)
    return facade, readings, automation


def test_missing_location_raises_not_found():
    facade, _, _ = make()
    with pytest.raises(NotFoundError):
        facade.get_overview(uuid4())


def test_no_saved_key_skips_evaluate():
    facade, readings, automation = make(key=None)
    overview = facade.get_overview(LOCATION_ID)
    assert overview.strategy_key is None and overview.last_recommendation is None
    assert automation.calls == 0
    assert readings.calls == [[SENSOR.id]]  # one batched reading lookup, not one per device


def test_saved_key_uses_evaluate_and_readings_carry_device_settings():
    facade, _, automation = make(key="conservative")
    overview = facade.get_overview(LOCATION_ID)
    assert automation.calls == 1
    assert overview.last_recommendation.action == "wait"
    [latest] = overview.zones[0].latest_readings
    assert (latest.value, latest.sampling_interval_seconds, latest.tracking_enabled) == (
        0.31, 120, True)
