# Strategy (Phase 6)

## Problem
Irrigation advice depends on a policy: one grower waits until the soil is really dry, another wants
to water earlier. If the API handler or one service held `if strategy == "conservative": ... elif ...`,
every new policy would mean editing that code, and the policies could not be tested or swapped on their own.

## Intent (my words)
Put each policy in its own class behind one interface, `decide(context)`. The service only chooses which
object to use (from the saved key) and calls it. Choosing the algorithm stays separate from running it.

## Participants
- Strategy interface: `AutomationStrategy.decide(context)`
- Concrete strategies: `ConservativeMoistureStrategy`, `AggressiveMoistureStrategy`
- Context: `LocationAutomationContext`, one zone's latest moisture plus that zone's low and high thresholds
- Client: `AutomationService`, which loads the saved key, builds one context per zone and calls `decide`

## How the two strategies differ
| Strategy | Irrigates when |
|----------|----------------|
| conservative | moisture is below the zone's low threshold |
| aggressive | moisture is below the midpoint of the zone's band, so it acts earlier |

Example from the running app: Bench 1 has a band of 0.20 to 0.45 (midpoint 0.325). At moisture 0.31,
conservative answers `wait` and aggressive answers `irrigate`. The same reading gives different advice.

## Persistence choice
The active strategy is stored in a dedicated `automation_rules` table, not as columns on `locations`.
Columns: `id`, `location_id` (UNIQUE, foreign key to `locations`, ON DELETE CASCADE), `strategy_key`,
`parameters` (JSONB), `updated_at`. The UNIQUE constraint allows one active strategy per location, and saving
uses an upsert (`ON CONFLICT (location_id) DO UPDATE`). There is no `greenhouse_id`.

## How evaluate works
1. Return 404 if the location does not exist.
2. Load the saved `strategy_key` from `automation_rules` (not from the request).
3. Load the location's zones and, for each zone, the latest moisture from sensors assigned to that zone.
4. Build one plain `LocationAutomationContext` per zone and call `get_strategy(key).decide(context)`.
5. Combine the zone results into one `action` and `reason`.

## Decisions the requirements left open
- Combining zones: the location answers `irrigate` if any zone says irrigate, and the reason names those
  zones. Otherwise it answers `wait` with every zone's reason.
- A zone with no assigned moisture sensor answers `wait` with the reason "no moisture sensor in this zone".
  It never borrows a reading from an unassigned device.
- No saved strategy: evaluate returns 400 ("save one first") instead of silently choosing a default.
- Unknown strategy key: rejected with 400 before `decide` runs, and nothing is saved.

## Where to look in code
- Interface and strategies: `domain/automation/strategy.py` (`get_strategy` is the registry lookup)
- Context: `domain/automation/context.py`
- Service: `application/automation/service.py`; DTOs: `application/automation/dto.py`
- Persistence: `infrastructure/persistence/models.py` (`AutomationRuleRow`) and `automation_repository.py`
- API: `interfaces/api/automation.py` (`PUT` save, `POST` evaluate under `/api/locations/{location_id}/automation`)
- UI: `frontend/src/features/automation/StrategyPanel.tsx`, mounted in `section-automation`

## Rules I followed
- Strategy classes import no SQLAlchemy or FastAPI, and no ORM rows are passed into `decide`.
- Thresholds come from the `zones` table, never from constants in a strategy.
- A strategy only recommends. It does not start a pump; carrying out the action belongs to a later pattern
  (Command).
- The router has no `if strategy == ...`; it only calls the service.

## Extension exercise
Add a third strategy, for example `frugal`, which irrigates only when moisture is below the low threshold minus
0.05. Steps: write a new class with its own `key` in `domain/automation/strategy.py`, register it in
`_STRATEGIES`, add its key to `STRATEGY_OPTIONS` in `StrategyPanel.tsx`, and add a unit test. The service, router
and database stay unchanged because `strategy_key` is just a short string (up to 32 characters).
