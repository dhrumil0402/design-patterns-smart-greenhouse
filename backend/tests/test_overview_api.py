import uuid

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)  # no "with": the sampler lifespan is not started in tests


def _new_sensor(kind="moisture") -> str:
    r = client.post("/api/sensors", json={"type": kind})
    assert r.status_code == 201
    return r.json()["id"]


def _seed_location() -> dict:
    name = f"Overview Site {uuid.uuid4().hex[:6]}"
    r = client.post(
        "/api/locations/config",
        json={
            "location_name": name,
            "zones": [
                {"name": "Bench 1", "moisture_threshold_low": 0.2, "moisture_threshold_high": 0.45},
                {"name": "Bench 2", "moisture_threshold_low": 0.3, "moisture_threshold_high": 0.6},
            ],
        },
    )
    assert r.status_code == 201
    body = r.json()
    zones = {zone["name"]: zone["id"] for zone in body["zones"]}
    return {"id": body["location"]["id"], "name": name, "bench1": zones["Bench 1"],
            "bench2": zones["Bench 2"]}


def test_overview_returns_strategy_and_readings():
    assert client.get(f"/api/locations/{uuid.uuid4()}/overview").status_code == 404

    site = _seed_location()
    try:
        # One assigned sensor in Bench 1 with its own sampling settings and a reading.
        assigned = _new_sensor("moisture")
        assert client.patch(f"/api/devices/{assigned}/zone",
                            json={"zone_id": site["bench1"]}).status_code == 200
        assert client.patch(f"/api/devices/{assigned}/sampling",
                            json={"sampling_interval_seconds": 45,
                                  "tracking_enabled": False}).status_code == 200
        reading = client.post(f"/api/sensors/{assigned}/read").json()

        # An unassigned sensor that also has a reading; it must not leak into the overview.
        unassigned = _new_sensor("moisture")
        client.post(f"/api/sensors/{unassigned}/read")

        url = f"/api/locations/{site['id']}/overview"
        response = client.get(url)
        assert response.status_code == 200
        body = response.json()

        assert body["location"] == {"id": site["id"], "name": site["name"]}
        assert body["strategy_key"] is None and body["last_recommendation"] is None
        assert body["device_counts"] == {"sensor": 1, "actuator": 0}

        zones = {zone["name"]: zone for zone in body["zones"]}
        assert set(zones) == {"Bench 1", "Bench 2"}
        for zone in body["zones"]:
            assert unassigned not in {device["id"] for device in zone["devices"]}
            assert unassigned not in {r["device_id"] for r in zone["latest_readings"]}

        bench1 = zones["Bench 1"]
        assert (bench1["moisture_threshold_low"], bench1["moisture_threshold_high"]) == (0.2, 0.45)
        assert [device["id"] for device in bench1["devices"]] == [assigned]
        assert bench1["devices"][0]["role"] == "sensor"
        [latest] = bench1["latest_readings"]
        assert latest["device_id"] == assigned
        assert latest["value"] == reading["value"] and latest["unit"] == reading["unit"]
        assert latest["tracking_enabled"] is False
        assert latest["sampling_interval_seconds"] == 45

        assert zones["Bench 2"]["devices"] == [] and zones["Bench 2"]["latest_readings"] == []

        # A newer reading shows up on the next GET.
        newer = client.post(f"/api/sensors/{assigned}/read").json()
        refreshed = {z["name"]: z for z in client.get(url).json()["zones"]}
        assert refreshed["Bench 1"]["latest_readings"][0]["recorded_at"] == newer["recorded_at"]

        # After saving a key, the recommendation matches evaluate for the same location.
        client.put(f"/api/locations/{site['id']}/automation", json={"strategy_key": "conservative"})
        saved = client.get(url).json()
        evaluated = client.post(f"/api/locations/{site['id']}/automation/evaluate").json()
        assert saved["strategy_key"] == "conservative"
        assert saved["last_recommendation"] == {
            "action": evaluated["action"], "reason": evaluated["reason"]}
    finally:
        client.delete(f"/api/locations/{site['id']}")
