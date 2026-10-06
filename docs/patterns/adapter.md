# Adapter (Phase 5)

## Problem
Sensors can speak different "dialects": our own simulation generator, a vendor SDK that returns scaled
integers and epoch seconds, and MQTT payload dicts. If services read these directly, every service learns
every dialect, and swapping a vendor means rewriting business code.

## Intent (my words)
Put each foreign dialect behind a small translator that implements an interface the application already
understands. The application talks to the port; only the adapter knows the foreign shape.

## Where to look in code
- Port (target): `domain/sensors/ports.py` (`SensorPort.read`), `domain/actuators/ports.py` (`ActuatorPort.apply`)
- Normalized value: `domain/sensors/reading.py` (`Reading`)
- Adapters: `infrastructure/adapters/sensors/` (simulation, vendor_stub, mqtt), `infrastructure/adapters/actuators/simulation.py`
- Selector (only place importing concrete adapters): `infrastructure/adapters/selector.py`
- Single writer: `application/readings/service.py` (`ReadingIngest`); sampler: `application/readings/sampler.py`

## Rules I followed
- Adapters translate only; irrigation decisions belong to Strategy (Phase 6).
- MQTT translation takes a dict; no broker connection in this phase.
- Every reading, whether manual or sampled, goes through `ReadingIngest`.

## Extension exercise
Add a third vendor (for example a CSV probe) as a new class implementing `SensorPort`, add one branch to the
selector, and write a test that its raw payload becomes a normalized `Reading`. No service code changes.
