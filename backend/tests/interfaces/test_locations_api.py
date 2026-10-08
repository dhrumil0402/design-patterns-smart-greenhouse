import uuid
from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from application.devices.zone_assignment_service import ZoneAssignmentService
from application.locations.config_service import LocationConfigService
from application.locations.zone_service import ZoneManagementService
from domain.devices.entity import Device
from domain.locations.entity import Location, LocationSummary, Zone
from interfaces.api import devices as devices_api
from interfaces.api import locations as locations_api
from main import app


class FakeStore:
    """Shared in-memory data so the two fake repositories see the same rows."""

    def __init__(self) -> None:
        self.locations: dict[uuid.UUID, str] = {}  # insertion order = creation order
        self.zones: dict[uuid.UUID, tuple[uuid.UUID, Zone]] = {}  # zone_id -> (location_id, zone)
        self.devices: dict[uuid.UUID, Device] = {}

    def clear_assignments(self, zone_id: uuid.UUID) -> None:
        for device_id, device in list(self.devices.items()):
            if device.zone_id == zone_id:
                self.devices[device_id] = replace(device, zone_id=None, location_id=None)


class FakeLocationRepository:
    """In-memory stand-in for LocationRepository."""

    def __init__(self, store: FakeStore) -> None:
        self._s = store

    def save_config(self, location: Location) -> Location:
        location_id = uuid.uuid4()
        self._s.locations[location_id] = location.name
        saved = []
        for zone in location.zones:
            with_id = replace(zone, id=uuid.uuid4())
            self._s.zones[with_id.id] = (location_id, with_id)
            saved.append(with_id)
        return Location(id=location_id, name=location.name, zones=tuple(saved))

    def get_config(self, location_id):
        if location_id not in self._s.locations:
            return None
        return Location(
            id=location_id,
            name=self._s.locations[location_id],
            zones=tuple(self.list_zones(location_id)),
        )

    def list_locations(self):
        return [LocationSummary(id=i, name=n) for i, n in reversed(self._s.locations.items())]

    def delete_location(self, location_id) -> bool:
        if location_id not in self._s.locations:
            return False
        for zone_id in [zid for zid, (lid, _) in self._s.zones.items() if lid == location_id]:
            self._s.clear_assignments(zone_id)
            del self._s.zones[zone_id]
        del self._s.locations[location_id]
        return True

    def location_exists(self, location_id) -> bool:
        return location_id in self._s.locations

    def list_zones(self, location_id):
        return [z for lid, z in self._s.zones.values() if lid == location_id]

    def add_zone(self, location_id, zone: Zone) -> Zone:
        saved = replace(zone, id=uuid.uuid4())
        self._s.zones[saved.id] = (location_id, saved)
        return saved

    def update_zone(self, location_id, zone_id, zone: Zone):
        entry = self._s.zones.get(zone_id)
        if entry is None or entry[0] != location_id:
            return None
        self._s.zones[zone_id] = (location_id, zone)
        return zone

    def delete_zone(self, location_id, zone_id) -> bool:
        entry = self._s.zones.get(zone_id)
        if entry is None or entry[0] != location_id:
            return False
        self._s.clear_assignments(zone_id)
        del self._s.zones[zone_id]
        return True

    def get_zone_location_id(self, zone_id):
        entry = self._s.zones.get(zone_id)
        return entry[0] if entry else None


class FakeDeviceRepository:
    """In-memory stand-in for the assignment methods of DeviceRepository."""

    def __init__(self, store: FakeStore) -> None:
        self._s = store

    def set_assignment(self, device_id, zone_id, location_id):
        device = self._s.devices.get(device_id)
        if device is None:
            return None
        updated = replace(device, zone_id=zone_id, location_id=location_id)
        self._s.devices[device_id] = updated
        return updated

    def list_devices_in_zone(self, zone_id):
        return [d for d in self._s.devices.values() if d.zone_id == zone_id]


@pytest.fixture(autouse=True)
def store():
    s = FakeStore()
    location_repo = FakeLocationRepository(s)
    device_repo = FakeDeviceRepository(s)
    overrides = {
        locations_api.get_service: lambda: LocationConfigService(location_repo),
        locations_api.get_zone_service: lambda: ZoneManagementService(location_repo),
        locations_api.get_assignment_service: lambda: ZoneAssignmentService(device_repo, location_repo),
        devices_api.get_assignment_service: lambda: ZoneAssignmentService(device_repo, location_repo),
    }
    app.dependency_overrides.update(overrides)
    yield s
    for dependency in overrides:
        app.dependency_overrides.pop(dependency, None)


client = TestClient(app)


def _zone(name, low=0.2, high=0.45, schedule=None):
    body = {"name": name, "moisture_threshold_low": low, "moisture_threshold_high": high}
    if schedule is not None:
        body["schedule"] = schedule
    return body


def _create_location(name="Lab Site A", zones=None):
    response = client.post(
        "/api/locations/config",
        json={"location_name": name, "zones": zones or [_zone("Z1")]},
    )
    assert response.status_code == 201
    return response.json()


def _add_device(store: FakeStore) -> uuid.UUID:
    device = Device(
        id=uuid.uuid4(),
        device_type="moisture_sensor",
        role="sensor",
        device_family="simulation",
        display_name="Test sensor",
        default_config={},
    )
    store.devices[device.id] = device
    return device.id


def _assign(device_id, zone_id):
    return client.patch(f"/api/devices/{device_id}/zone", json={"zone_id": zone_id})


# --- create, read, list ---


def test_create_config_persists_location_and_zones():
    body = _create_location(zones=[_zone("Z1"), _zone("Z2", 0.15, 0.35)])
    location_id = body["location"]["id"]
    assert all(z["location_id"] == location_id for z in body["zones"])

    fetched = client.get(f"/api/locations/{location_id}/config")
    assert fetched.status_code == 200
    assert fetched.json()["location"]["name"] == "Lab Site A"
    assert len(fetched.json()["zones"]) == 2


def test_invalid_config_returns_400_and_saves_nothing():
    response = client.post(
        "/api/locations/config",
        json={"location_name": "Bad", "zones": [_zone("Z1", 0.5, 0.3)]},
    )
    assert response.status_code == 400
    assert client.get("/api/locations").json() == []


def test_get_missing_location_returns_404():
    assert client.get(f"/api/locations/{uuid.uuid4()}/config").status_code == 404


def test_list_locations():
    assert client.get("/api/locations").json() == []
    _create_location("Site A")
    _create_location("Site B")
    names = [item["name"] for item in client.get("/api/locations").json()]
    assert names == ["Site B", "Site A"]  # newest first


# --- zone assignment ---


def test_assign_devices_to_zone(store):
    location = _create_location(zones=[_zone("Z1"), _zone("Z2", 0.15, 0.35)])
    location_id = location["location"]["id"]
    z1, z2 = location["zones"][0]["id"], location["zones"][1]["id"]
    in_z2 = [_add_device(store), _add_device(store)]
    in_z1 = _add_device(store)
    _add_device(store)  # stays unassigned

    for device_id in in_z2:
        response = _assign(device_id, z2)
        assert response.status_code == 200
        assert response.json()["zone_id"] == z2
        assert response.json()["location_id"] == location_id
    assert _assign(in_z1, z1).status_code == 200

    listed = client.get(f"/api/locations/{location_id}/zones/{z2}/devices")
    assert listed.status_code == 200
    assert {d["id"] for d in listed.json()} == {str(d) for d in in_z2}


def test_unassign_clears_zone_and_location(store):
    location = _create_location()
    zone_id = location["zones"][0]["id"]
    device_id = _add_device(store)
    assert _assign(device_id, zone_id).status_code == 200

    response = _assign(device_id, None)
    assert response.status_code == 200
    assert response.json()["zone_id"] is None
    assert response.json()["location_id"] is None


def test_assignment_returns_404_for_missing_things(store):
    location = _create_location()
    zone_id = location["zones"][0]["id"]
    device_id = _add_device(store)

    assert _assign(uuid.uuid4(), zone_id).status_code == 404  # missing device
    assert _assign(device_id, str(uuid.uuid4())).status_code == 404  # missing zone
    wrong_location = client.get(f"/api/locations/{uuid.uuid4()}/zones/{zone_id}/devices")
    assert wrong_location.status_code == 404  # zone is not in that location


# --- delete location ---


def test_delete_location_clears_assignments(store):
    site_a = _create_location("Site A")
    _create_location("Site B")
    device_id = _add_device(store)
    assert _assign(device_id, site_a["zones"][0]["id"]).status_code == 200
    a_id = site_a["location"]["id"]

    assert client.delete(f"/api/locations/{a_id}").status_code == 204
    assert client.get(f"/api/locations/{a_id}/config").status_code == 404
    assert [item["name"] for item in client.get("/api/locations").json()] == ["Site B"]
    assert store.devices[device_id].zone_id is None
    assert store.devices[device_id].location_id is None
    assert client.delete(f"/api/locations/{a_id}").status_code == 404


# --- zone management ---


def test_add_zone_to_location():
    location_id = _create_location()["location"]["id"]
    url = f"/api/locations/{location_id}/zones"

    response = client.post(url, json=_zone("Z2", 0.15, 0.35))
    assert response.status_code == 201
    assert response.json()["location_id"] == location_id
    assert len(client.get(f"/api/locations/{location_id}/config").json()["zones"]) == 2

    assert client.post(url, json=_zone("z2")).status_code == 400  # duplicate name
    missing = client.post(f"/api/locations/{uuid.uuid4()}/zones", json=_zone("Zx"))
    assert missing.status_code == 404


def test_update_zone_rejects_invalid_thresholds():
    location = _create_location(zones=[_zone("Z1", schedule={"watering": "08:00"})])
    url = f"/api/locations/{location['location']['id']}/zones/{location['zones'][0]['id']}"

    bad = client.patch(
        url, json={"name": "Z1", "moisture_threshold_low": 0.6, "moisture_threshold_high": 0.3}
    )
    assert bad.status_code == 400

    good = client.patch(
        url,
        json={"name": "Z1 renamed", "moisture_threshold_low": 0.1, "moisture_threshold_high": 0.5},
    )
    assert good.status_code == 200
    assert good.json()["name"] == "Z1 renamed"
    assert good.json()["schedule"] == {"watering": "08:00"}  # omitted schedule is kept


def test_delete_zone_clears_assignments(store):
    location = _create_location(zones=[_zone("Z1"), _zone("Z2", 0.15, 0.35)])
    location_id = location["location"]["id"]
    z2 = location["zones"][1]["id"]
    device_id = _add_device(store)
    assert _assign(device_id, z2).status_code == 200

    assert client.delete(f"/api/locations/{location_id}/zones/{z2}").status_code == 204
    assert len(client.get(f"/api/locations/{location_id}/config").json()["zones"]) == 1
    assert store.devices[device_id].zone_id is None
    assert store.devices[device_id].location_id is None


def test_delete_last_zone_is_rejected():
    location = _create_location()
    location_id = location["location"]["id"]
    zone_id = location["zones"][0]["id"]

    response = client.delete(f"/api/locations/{location_id}/zones/{zone_id}")
    assert response.status_code == 400
    assert len(client.get(f"/api/locations/{location_id}/config").json()["zones"]) == 1