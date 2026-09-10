import uuid

from fastapi.testclient import TestClient

from application.sensors.service import SensorService
from domain.sensors.entity import Sensor
from interfaces.api.sensors import get_sensor_service
from main import app


class FakeRepository:
    """In-memory stand-in for DeviceRepository, so this test needs no database."""

    def __init__(self) -> None:
        self._rows: list[Sensor] = []

    def add(self, sensor: Sensor) -> Sensor:
        sensor.id = uuid.uuid4()
        self._rows.append(sensor)
        return sensor

    def list_sensors(self) -> list[Sensor]:
        return list(self._rows)

    def get_by_id(self, sensor_id):
        return next((s for s in self._rows if s.id == sensor_id), None)


def _override_service():
    return SensorService(FakeRepository())


app.dependency_overrides[get_sensor_service] = _override_service
client = TestClient(app)


def test_list_sensors_starts_empty():
    app.dependency_overrides[get_sensor_service] = _override_service
    response = client.get("/api/sensors")
    assert response.status_code == 200
    assert response.json() == []


def test_create_moisture_and_light_return_distinct_configs():
    app.dependency_overrides[get_sensor_service] = _override_service
    moisture_resp = client.post("/api/sensors", json={"type": "moisture"})
    light_resp = client.post("/api/sensors", json={"type": "light"})

    assert moisture_resp.status_code == 201
    assert light_resp.status_code == 201
    assert moisture_resp.json()["default_config"] != light_resp.json()["default_config"]


def test_create_unknown_type_returns_400():
    app.dependency_overrides[get_sensor_service] = _override_service
    response = client.post("/api/sensors", json={"type": "temperature"})
    assert response.status_code == 400
    assert "temperature" in response.json()["detail"]
