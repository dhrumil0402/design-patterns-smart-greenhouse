# Abstract Factory — Device families

## Problem

Sensors and actuators need to be provisioned as a **coherent kit** per environment
(`simulation` for local dev, `edge` for stub hardware). If each device were selected
with its own independent `if family == ...` check, nothing would stop a simulation
sensor from being paired with an edge actuator — an inconsistent, hard-to-debug kit.

## Solution

`DeviceFamilyFactory` is an abstract factory with one method, `create_device_set()`,
that returns a matching list of `Device` objects (2 sensors + 2 actuators) all
tagged with the same `device_family`. `SimulationDeviceFactory` and
`EdgeHardwareFactory` are the concrete factories; `get_family_factory(key)` is the
registry callers use instead of constructing a concrete factory by name.

Each concrete factory **composes** the Phase 2 Factory Method creators
(`MoistureSensorCreator`, `LightSensorCreator`) to build its sensors, then wraps
the result into a `Device` and adds family-specific actuator entries. Sensor
defaults are not duplicated — they still live in the Phase 2 creators.

## Where in code

- `backend/src/domain/devices/family_factory.py` — `DeviceFamilyFactory`,
  `SimulationDeviceFactory`, `EdgeHardwareFactory`, `get_family_factory`
- `backend/src/domain/devices/entity.py` — the `Device` entity (covers both
  `role="sensor"` and `role="actuator"`)
- `backend/src/application/devices/family_service.py` — `DeviceFamilyService`,
  the only caller of `get_family_factory`
- `backend/src/interfaces/api/devices.py` — `POST /api/devices/provision`,
  `GET /api/devices`

## Factory Method vs Abstract Factory

Factory Method (Phase 2) answers "which **one** product?" — moisture sensor or
light sensor. Abstract Factory (this phase) answers "which **product line**?" —
simulation kit or edge kit — and internally uses Factory Method creators to build
the individual sensors in that kit.

## Extension exercise

Add a third family, e.g. `greenhouse-pro`, with a `SoilNutrientSensorCreator` as
a third sensor type not present in the other two families. Register it in
`get_family_factory` and confirm `create_device_set()` still returns a
family-consistent kit without changing `DeviceFamilyService` or the API router.
