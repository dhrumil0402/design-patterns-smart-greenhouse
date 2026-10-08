import uuid

import pytest
from fastapi.testclient import TestClient

from application.automation.service import AutomationService
from domain.locations.entity import Zone
from interfaces.api import automation as automation_api
from main import app

LOCATION_ID = uuid.uuid4()
ZONE = Zone(
    id=uuid.uuid4(),
    name="Bench 1",
    moisture_threshold_low=0.25,
    moisture_threshold_high=0.45,
    schedule={},
)


class FakeLocations:
    """In-memory stand-in for the LocationRepository methods the service uses."""

    def location_exists(self, location_id):
        return location_id == LOCATION_ID

    def list_zones(self, location_id):
        return [ZONE] if location_id == LOCATION_ID else []


class FakeRules:
    """In-memory stand-in for AutomationRepository. The zone's latest moisture is 0.30."""

    def __init__(self, moisture=0.30):
        self.keys = {}
        self.moisture = moisture

    def get_strategy_key(self, location_id):
        return self.keys.get(location_id)

    def upsert_strategy_key(self, location_id, key):
        self.keys[location_id] = key

    def latest_moisture_by_zone(self, zone_ids):
        return {ZONE.id: self.moisture} if ZONE.id in zone_ids else {}


@pytest.fixture(autouse=True)
def rules():
    fake = FakeRules()
    app.dependency_overrides[automation_api.get_service] = lambda: AutomationService(
        FakeLocations(), fake
    )
    yield fake
    app.dependency_overrides.pop(automation_api.get_service, None)


client = TestClient(app)
SAVE = f"/api/locations/{LOCATION_ID}/automation"
EVALUATE = f"{SAVE}/evaluate"


def test_save_strategy_returns_the_saved_key(rules):
    response = client.put(SAVE, json={"strategy_key": "conservative"})
    assert response.status_code == 200
    assert response.json() == {"location_id": str(LOCATION_ID), "strategy_key": "conservative"}
    assert rules.keys[LOCATION_ID] == "conservative"


def test_evaluate_uses_the_saved_key_and_changes_with_it():
    client.put(SAVE, json={"strategy_key": "conservative"})
    first = client.post(EVALUATE)
    client.put(SAVE, json={"strategy_key": "aggressive"})
    second = client.post(EVALUATE)

    assert first.status_code == 200 and second.status_code == 200
    # Same moisture (0.30), different saved key, different recommendation.
    assert (first.json()["strategy_key"], first.json()["action"]) == ("conservative", "wait")
    assert (second.json()["strategy_key"], second.json()["action"]) == ("aggressive", "irrigate")
    assert set(second.json()) == {"location_id", "strategy_key", "action", "reason"}


def test_unknown_strategy_key_returns_400_and_saves_nothing(rules):
    response = client.put(SAVE, json={"strategy_key": "yolo"})
    assert response.status_code == 400
    assert rules.keys == {}


def test_evaluate_without_a_saved_strategy_returns_400():
    assert client.post(EVALUATE).status_code == 400


def test_missing_location_returns_404():
    missing = f"/api/locations/{uuid.uuid4()}/automation"
    assert client.put(missing, json={"strategy_key": "conservative"}).status_code == 404
    assert client.post(f"{missing}/evaluate").status_code == 404
