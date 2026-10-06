from fastapi.testclient import TestClient

from main import app

client = TestClient(app)  # no "with": the sampler lifespan is not started in tests
MISSING = "00000000-0000-0000-0000-000000000000"


def _new_sensor(kind="moisture") -> str:
    r = client.post("/api/sensors", json={"type": kind})
    assert r.status_code == 201
    return r.json()["id"]


def test_read_appends_rows_and_returns_normalized_dto():
    sid = _new_sensor("moisture")
    first = client.post(f"/api/sensors/{sid}/read")
    assert first.status_code == 201
    body = first.json()
    assert body["device_id"] == sid and body["source"] == "simulation" and body["unit"] == "vwc"
    assert 0.2 <= body["value"] <= 0.6
    client.post(f"/api/sensors/{sid}/read")
    history = client.get(f"/api/sensors/{sid}/readings?limit=10").json()
    assert len(history) == 2  # history appends, newest first
    assert history[0]["recorded_at"] >= history[1]["recorded_at"]


def test_read_missing_device_is_404():
    assert client.post(f"/api/sensors/{MISSING}/read").status_code == 404
    assert client.get(f"/api/sensors/{MISSING}/readings").status_code == 404


def test_mqtt_sensor_cannot_one_shot_read():
    kit = client.post("/api/devices/provision?family=edge").json()
    mqtt_sensor = next(d for d in kit if d["role"] == "sensor")
    r = client.post(f"/api/sensors/{mqtt_sensor['id']}/read")
    assert r.status_code == 400


def test_sampling_patch_round_trip_and_minimum():
    sid = _new_sensor("light")
    assert client.get(f"/api/devices/{sid}/sampling").json() == {
        "sampling_interval_seconds": 60, "tracking_enabled": True}
    ok = client.patch(f"/api/devices/{sid}/sampling",
                      json={"sampling_interval_seconds": 30, "tracking_enabled": False})
    assert ok.status_code == 200
    assert client.get(f"/api/devices/{sid}/sampling").json() == {
        "sampling_interval_seconds": 30, "tracking_enabled": False}
    too_small = client.patch(f"/api/devices/{sid}/sampling",
                             json={"sampling_interval_seconds": 4, "tracking_enabled": True})
    assert too_small.status_code == 400
    assert client.patch(f"/api/devices/{MISSING}/sampling",
                        json={"sampling_interval_seconds": 30, "tracking_enabled": True}).status_code == 404
