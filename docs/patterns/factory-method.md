# Factory Method — Sensor Creation

## Problem

The Smart Greenhouse needs to support multiple kinds of sensors (moisture,
light, and more later) that each need different default settings — a
moisture sensor cares about a threshold percentage and samples every 5
minutes, while a light sensor uses a different unit and samples every
minute. Without a pattern, every place that needs to create a sensor (the
API layer, tests, seed scripts) would end up with its own `if type ==
"moisture": ... elif type == "light": ...` block, duplicating the same
defaults and getting out of sync as more sensor types are added.

## Solution

We used the **Factory Method** pattern. `SensorCreator` is an abstract
base class with one method, `create_sensor()`. Each concrete sensor type
gets its own creator subclass (`MoistureSensorCreator`,
`LightSensorCreator`) that knows how to build a `Sensor` with the right
`device_type` and `default_config` for that type. A small registry
function, `get_creator(sensor_type)`, maps a short string key (`"moisture"`,
`"light"`) to the right creator instance, and raises a `ValueError` for
anything unrecognized.

Callers — the application service, the API router, tests — never
construct a `MoistureSensor` or `LightSensor` directly. They ask
`get_creator(type)` for a creator and call `.create_sensor()` on it. This
means:

- Adding a new sensor type means adding one new creator class and one
  registry entry — nothing else in the codebase changes.
- The domain layer (`Sensor`, `SensorCreator`, and its subclasses) has no
  dependency on FastAPI, SQLAlchemy, or Pydantic — it's plain Python and
  can be tested and reused without any of those.
- Unknown sensor types are rejected in the domain/application layer,
  before any database work happens, so we never attempt a useless insert.

## Where to look in code

| What | File |
|------|------|
| `Sensor` entity | `backend/src/domain/sensors/entity.py` |
| `SensorCreator` abstract base + concrete creators | `backend/src/domain/sensors/creators.py` |
| `get_creator` registry | `backend/src/domain/sensors/creators.py` |
| Application service using the creators | `backend/src/application/sensors/service.py` |
| Repository persisting the result | `backend/src/infrastructure/persistence/device_repository.py` |
| API router calling into the service | `backend/src/interfaces/api/sensors.py` |
| Unit tests for the creators | `backend/tests/domain/test_sensor_creators.py` |

## Extension exercise

Try adding a **temperature sensor**:

1. Add `TemperatureSensorCreator(SensorCreator)` in `creators.py`, returning
   a `Sensor` with `device_type="temperature_sensor"` and a
   `default_config` using a `unit` of `"celsius"` and its own reasonable
   `sampling_interval_seconds`.
2. Register it in `_CREATORS` under the key `"temperature"`.
3. Add a unit test asserting its `default_config` is distinct from both
   moisture and light.
4. Add a "Add temperature sensor" button in the frontend `SensorList`
   component, following the same pattern as the existing two buttons.

Nothing else needs to change — not the repository, not the API router, not
the database schema — because those all depend only on the `SensorCreator`
interface and the `Sensor` entity, not on which concrete sensor type is
being created.
