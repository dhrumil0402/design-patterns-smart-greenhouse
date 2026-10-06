from __future__ import annotations

from domain.actuators.ports import ActuatorPort
from domain.devices.entity import Device
from domain.sensors.ports import SensorPort
from infrastructure.adapters.actuators.simulation import SimulationActuatorAdapter
from infrastructure.adapters.sensors.simulation import SimulationSensorAdapter
from infrastructure.adapters.sensors.vendor_stub import VendorStubSensorAdapter

_ACTUATOR = SimulationActuatorAdapter()


def select_sensor_adapter(device: Device) -> SensorPort:
    """Selection rule (documented):
      1. default_config["adapter"] == "vendor"  -> VendorStubSensorAdapter
      2. default_config["protocol"] == "simulation" -> SimulationSensorAdapter
      3. default_config["protocol"] == "mqtt" -> no one-shot read (push-only)
    The separate "adapter" flag keeps the vendor stub from colliding with
    the two protocol values.
    """
    cfg = device.default_config or {}
    if cfg.get("adapter") == "vendor":
        return VendorStubSensorAdapter()
    protocol = cfg.get("protocol")
    if protocol == "simulation":
        return SimulationSensorAdapter()
    if protocol == "mqtt":
        raise ValueError("mqtt devices push readings; a one-shot read is not available")
    raise ValueError(f"no sensor adapter for protocol {protocol!r}")


def select_actuator_adapter(device: Device) -> ActuatorPort:
    """Only the simulation actuator exists in this phase (no GPIO)."""
    return _ACTUATOR
