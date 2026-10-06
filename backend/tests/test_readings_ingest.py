import random
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from application.readings.sampler import SimulationSampler
from application.readings.service import DeviceNotFoundError, ReadingIngest
from domain.devices.entity import Device
from domain.sensors.reading import Reading
from infrastructure.adapters.sensors.simulation import SimulationSensorAdapter


def make_device(device_type="moisture_sensor", role="sensor", protocol="simulation", interval=60, tracking=True):
    return Device(
        id=uuid4(), device_type=device_type, role=role, device_family="simulation",
        display_name="t", default_config={"protocol": protocol},
        sampling_interval_seconds=interval, tracking_enabled=tracking,
    )


class FakeDeviceRepo:
    def __init__(self, devices):
        self._d = {d.id: d for d in devices}

    def get_device(self, device_id):
        return self._d.get(device_id)

    def list_devices(self, *, device_family=None, role=None):
        return [d for d in self._d.values() if role is None or d.role == role]


class FakeReadingRepo:
    def __init__(self):
        self.rows = []

    def insert(self, reading):
        self.rows.append(reading)
        return reading

    def list_for_device(self, device_id, limit=20):
        rows = [r for r in self.rows if r.device_id == device_id]
        return sorted(rows, key=lambda r: r.recorded_at, reverse=True)[:limit]

    def latest_recorded_at(self, device_id):
        times = [r.recorded_at for r in self.rows if r.device_id == device_id]
        return max(times) if times else None


def selector(device):
    return SimulationSensorAdapter(random.Random(1))


def build(devices):
    devs, reads = FakeDeviceRepo(devices), FakeReadingRepo()
    ingest = ReadingIngest(devs, reads, selector)
    sampler = SimulationSampler(devs, reads, ingest, selector)
    return reads, ingest, sampler


def count(reads, device):
    return len([r for r in reads.rows if r.device_id == device.id])


def test_take_reading_persists_and_returns_dto():
    dev = make_device()
    reads, ingest, _ = build([dev])
    dto = ingest.take_reading(dev.id)
    assert dto.device_id == dev.id and dto.source == "simulation" and dto.unit == "vwc"
    assert count(reads, dev) == 1
    ingest.take_reading(dev.id)
    assert count(reads, dev) == 2  # history appends


def test_take_reading_missing_device_raises_not_found():
    _, ingest, _ = build([])
    with pytest.raises(DeviceNotFoundError):
        ingest.take_reading(uuid4())


def test_take_reading_rejects_actuator():
    pump = make_device("water_pump", role="actuator")
    _, ingest, _ = build([pump])
    with pytest.raises(ValueError):
        ingest.take_reading(pump.id)


def test_record_persists_translated_reading():
    dev = make_device(protocol="mqtt")
    reads, ingest, _ = build([dev])
    reading = Reading(dev.id, 0.41, "vwc", "mqtt", datetime.now(timezone.utc))
    dto = ingest.record(dev.id, reading)
    assert dto.source == "mqtt" and count(reads, dev) == 1


def test_sampler_respects_interval_and_tracking():
    tracked = make_device(interval=60)
    untracked = make_device(tracking=False)
    mqtt_dev = make_device(protocol="mqtt")
    pump = make_device("water_pump", role="actuator")
    reads, _, sampler = build([tracked, untracked, mqtt_dev, pump])

    t0 = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    assert sampler.run_once(t0) == 1
    assert count(reads, tracked) == 1

    sampler.run_once(t0 + timedelta(seconds=30))   # inside interval
    assert count(reads, tracked) == 1

    sampler.run_once(t0 + timedelta(seconds=61))   # interval elapsed
    assert count(reads, tracked) == 2

    for skipped in (untracked, mqtt_dev, pump):
        assert count(reads, skipped) == 0
