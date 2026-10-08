from uuid import uuid4

import pytest

from application.automation.errors import StrategyNotSetError
from application.automation.service import AutomationService
from application.locations.errors import NotFoundError
from domain.locations.entity import Zone


class FakeLocations:
    """In-memory stand-in for the two LocationRepository methods the service uses."""

    def __init__(self, location_id=None, zones=()):
        self._location_id = location_id
        self._zones = list(zones)

    def location_exists(self, location_id):
        return location_id == self._location_id

    def list_zones(self, location_id):
        return list(self._zones) if self.location_exists(location_id) else []


class FakeRules:
    """In-memory stand-in for AutomationRepository."""

    def __init__(self, moisture=None):
        self.keys = {}
        self.moisture = moisture or {}

    def get_strategy_key(self, location_id):
        return self.keys.get(location_id)

    def upsert_strategy_key(self, location_id, key):
        self.keys[location_id] = key

    def latest_moisture_by_zone(self, zone_ids):
        return {z: v for z, v in self.moisture.items() if z in zone_ids}


def build(*moistures):
    """One zone per value (band 0.25-0.45). None means that zone has no moisture sensor."""
    zones = [
        Zone(id=uuid4(), name=f"Zone {i + 1}", moisture_threshold_low=0.25,
             moisture_threshold_high=0.45, schedule={})
        for i in range(len(moistures))
    ]
    location_id = uuid4()
    rules = FakeRules({z.id: m for z, m in zip(zones, moistures) if m is not None})
    return AutomationService(FakeLocations(location_id, zones), rules), location_id, rules


def test_missing_location_is_not_found():
    service = AutomationService(FakeLocations(), FakeRules())
    with pytest.raises(NotFoundError):
        service.evaluate(uuid4())
    with pytest.raises(NotFoundError):
        service.set_strategy(uuid4(), "conservative")


def test_evaluate_requires_a_saved_strategy():
    service, location_id, _ = build(0.30)
    with pytest.raises(StrategyNotSetError):
        service.evaluate(location_id)


def test_unknown_key_is_rejected_and_not_saved():
    service, location_id, rules = build(0.30)
    with pytest.raises(ValueError):
        service.set_strategy(location_id, "yolo")
    assert rules.keys == {}


def test_evaluate_uses_the_persisted_key():
    service, location_id, _ = build(0.30)  # inside the band, but below the midpoint 0.35
    service.set_strategy(location_id, "conservative")
    first = service.evaluate(location_id)
    service.set_strategy(location_id, "aggressive")
    second = service.evaluate(location_id)
    assert (first.strategy_key, first.action) == ("conservative", "wait")
    assert (second.strategy_key, second.action) == ("aggressive", "irrigate")


def test_zone_without_sensor_waits():
    service, location_id, _ = build(None)
    service.set_strategy(location_id, "conservative")
    result = service.evaluate(location_id)
    assert result.action == "wait" and "no moisture sensor" in result.reason


def test_one_dry_zone_makes_the_location_irrigate():
    service, location_id, _ = build(0.40, 0.10)
    service.set_strategy(location_id, "conservative")
    result = service.evaluate(location_id)
    assert result.action == "irrigate"
    assert "Zone 2" in result.reason and "Zone 1" not in result.reason
