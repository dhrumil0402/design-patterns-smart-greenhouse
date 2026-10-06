import random
from uuid import uuid4

import pytest

from domain.devices.entity import Device
from infrastructure.adapters.actuators.simulation import SimulationActuatorAdapter
from infrastructure.adapters.selector import select_sensor_adapter
from infrastructure.adapters.sensors.mqtt import MqttSensorAdapter
from infrastructure.adapters.sensors.simulation import SimulationSensorAdapter
from infrastructure.adapters.sensors.vendor_stub import VendorStubSensorAdapter


def make_device(device_type="moisture_sensor", config=None) -> Device:
    return Device(
        id=uuid4(),
        device_type=device_type,
        role="sensor",
        device_family="simulation",
        display_name="test",
        default_config=config or {},
    )


class FakeVendorClient:
    def __init__(self, payload):
        self._payload = payload

    def poll(self, probe_id, device_type):
        return self._payload


def test_vendor_adapter_normalizes_raw_payload():
    raw = {"probe": "p1", "data": {"v": 3120, "u": "pct_x100"}, "epoch": 1_700_000_000}
    reading = VendorStubSensorAdapter(FakeVendorClient(raw)).read(make_device())
    assert reading.value == 0.312
    assert reading.unit == "vwc"
    assert reading.source == "vendor"
    assert reading.recorded_at.tzinfo is not None


def test_vendor_adapter_rejects_unknown_unit():
    raw = {"probe": "p1", "data": {"v": 1, "u": "furlongs"}, "epoch": 1_700_000_000}
    with pytest.raises(ValueError):
        VendorStubSensorAdapter(FakeVendorClient(raw)).read(make_device())


def test_simulation_adapter_value_in_range():
    adapter = SimulationSensorAdapter(random.Random(1))
    for _ in range(50):
        m = adapter.read(make_device("moisture_sensor"))
        assert 0.2 <= m.value <= 0.6 and m.unit == "vwc" and m.source == "simulation"
        l = adapter.read(make_device("light_sensor"))
        assert 200 <= l.value <= 2000 and l.unit == "lux"


def test_mqtt_adapter_translates_payload():
    reading = MqttSensorAdapter().translate(make_device(), {"value": 0.41, "unit": "vwc"})
    assert reading.value == 0.41
    assert reading.unit == "vwc"
    assert reading.source == "mqtt"


@pytest.mark.parametrize("payload", [{}, {"value": "x", "unit": "vwc"}, {"value": 1}, {"value": True, "unit": "vwc"}])
def test_mqtt_adapter_rejects_bad_payload(payload):
    with pytest.raises(ValueError):
        MqttSensorAdapter().translate(make_device(), payload)


def test_selector_follows_documented_rule():
    sim = make_device(config={"protocol": "simulation"})
    vendor = make_device(config={"protocol": "simulation", "adapter": "vendor"})
    assert isinstance(select_sensor_adapter(sim), SimulationSensorAdapter)
    assert isinstance(select_sensor_adapter(vendor), VendorStubSensorAdapter)
    with pytest.raises(ValueError):
        select_sensor_adapter(make_device(config={"protocol": "mqtt"}))


def test_actuator_adapter_records_intent():
    adapter = SimulationActuatorAdapter()
    device_id = uuid4()
    adapter.apply(device_id, "start_pump", {"seconds": 5})
    assert adapter.applied == [(device_id, "start_pump", {"seconds": 5})]
