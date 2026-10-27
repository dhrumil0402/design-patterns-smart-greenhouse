# Facade (Phase 7)

## Problem
The dashboard wants one snapshot of a location: its zones, which devices sit in each zone, the newest
reading of those devices, the saved strategy and what that strategy recommends right now. That data lives
in five places (locations, zones, devices, sensor_readings, automation_rules) and needs the automation
service to compute the recommendation. If the HTTP handler or the React page did that work, every screen
that needs a snapshot would repeat the same multi-step dance and the same "assigned device" rules.

## Intent (my words)
Give the overview one simple entry point, `LocationOverviewFacade.get_overview(location_id)`, that calls the
existing subsystems in the right order and returns one read model. The callers do not need to know which
repositories exist or how they fit together.

## Participants
- Facade: `LocationOverviewFacade` in `application/overview/facade.py`
- Read model: `LocationOverviewDto` and its parts in `application/overview/dto.py`
- Subsystems it hides:
  - `LocationRepository.get_config`: the location and every zone
  - `DeviceRepository.list_assigned_devices`: devices with this `location_id` and a non-null `zone_id`
  - `ReadingRepository.latest_for_devices`: newest `sensor_readings` row per device
  - `AutomationRepository.get_strategy_key`: the saved key
  - `AutomationService.evaluate`: the Phase 6 Strategy client, which calls `decide`
- Client: `GET /api/locations/{location_id}/overview` (`interfaces/api/overview.py`) and the dashboard
  `OverviewPanel` in `#overview`

## Why one entry point
- The router's only collaborator is the facade. It does not import a repository; the wiring lives in
  `infrastructure/overview_factory.py`. The handler maps `NotFoundError` to 404 and nothing else.
- The React panel makes one `fetchOverview(locationId)` call and Refresh repeats it. It never merges device,
  reading and automation responses, so the "assigned only" and "newest reading" rules live in one place.
- The facade only orchestrates. Irrigation policy stays in the strategies, sensor translation stays in the
  Phase 5 adapters, and SQL stays in the repositories.

## The recommendation is computed, not cached
`last_recommendation` is produced on every GET by calling the existing `AutomationService.evaluate`. It is
never written to a table. If no key is saved, the facade skips evaluate and returns HTTP 200 with
`strategy_key` and `last_recommendation` both null (it is not a 404 and not a 400). So a new reading or a
newly saved key shows up on the very next overview GET.

## Query shape
1. One load of the location and its zones (`get_config`).
2. One query for all assigned devices of the location.
3. One query for the newest reading of those device ids, using PostgreSQL `DISTINCT ON (device_id)` ordered by
   `recorded_at DESC`. Any source counts (manual read, sampler, MQTT); there is no `source` filter.
4. One read of the saved strategy key.
5. `evaluate` only when a key exists.

Devices and readings are grouped by zone in Python from those two result sets, so there is no reading query
per device (no N+1). `evaluate` itself re-checks the location, loads the zones again and looks up the latest
moisture per zone with one query (`latest_moisture_by_zone`). I left that inside the strategy service on
purpose instead of reimplementing `decide` in the facade to save those few queries.

## Rules for the read model
- Every zone of the location is listed, even one with no devices (`devices: []`, `latest_readings: []`).
- Unassigned devices (no `zone_id`) are not counted and never appear in any zone.
- A device with no reading stays in `devices` and is left out of `latest_readings`.
- `tracking_enabled` and `sampling_interval_seconds` on a reading are copied from the device; they were not
  added to `sensor_readings`.
- Overview is scoped by `location_id`; there is no `greenhouse_id`.

## Database
No new table and no migration. I skipped the optional `location_overview_v1` view because the existing tables
from Phases 2 to 6 (`locations`, `zones`, `devices`, `sensor_readings`, `automation_rules`) are enough.

## Where to look in code
- Facade and DTOs: `backend/src/application/overview/`
- New repository queries: `DeviceRepository.list_assigned_devices`, `ReadingRepository.latest_for_devices`
- Wiring: `backend/src/infrastructure/overview_factory.py`
- API: `backend/src/interfaces/api/overview.py`
- UI: `frontend/src/components/overview/OverviewPanel.tsx`, mounted in `#overview`
- Tests: `backend/tests/test_overview_api.py` (seeded database), `backend/tests/test_overview_facade.py` (fakes)
