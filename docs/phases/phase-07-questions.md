# Phase 7 — Facade questions

**Pattern / focus:** Facade.


## A. Pattern

1. State the intent of Facade in plain language. What problem appears when every HTTP handler (or every UI screen) repeats the same multi-step dance across repositories and services?

> [!NOTE]
> **_Your Answer_**
>
> Facade is basically one simple entry point in front of a bunch of other classes. The caller just asks for what it needs and the facade deals with calling everything else in the right order, so the caller doesn't have to know how all the parts connect.
>
> If we didn't have it, every handler or screen that needs the location overview would have to load the location, then the zones, then the devices, then the readings, then the strategy and then call evaluate. That's a lot of steps to repeat, and the rules like "only count assigned devices" would be copied everywhere. After a while one copy would end up slightly different from the others, and if the query changes you have to go and fix it in every place.

2. A facade **orchestrates** collaborators. What should it **not** become (a god object that owns all domain logic)? Where should irrigation policy, sensor translation, and persistence stay instead?

> [!NOTE]
> **_Your Answer_**
>
> It shouldn't turn into a god object that does everything itself, like writing SQL, deciding when to irrigate or reading sensor payloads. In my code `LocationOverviewFacade` only calls other objects and puts their results together into the DTO.
>
> The irrigation policy still stays in the strategies from Phase 6, and the facade only reaches it by calling `AutomationService.evaluate`. Sensor translation stays in the Phase 5 adapters. Persistence stays in the repositories, which is also why I put the new queries (assigned devices and latest reading per device) in `DeviceRepository` and `ReadingRepository` and not in the facade.

3. When should you use Facade, and when should you skip it (a single repository call is enough; or you actually need to **translate** a mismatched interface)?

> [!NOTE]
> **_Your Answer_**
>
> I think it makes sense when the client needs something that takes several subsystems working together, and that coordination would otherwise be repeated in more than one place. The overview is a good case for this because it pulls data from five tables and also needs the automation service.
>
> If one repository call already gives you what you need, like just listing the locations, then a facade is only an extra layer for no real reason. And if the actual problem is that some interface doesn't match what our code expects, then that's more of an Adapter problem than a Facade one.

## B. This phase of the application

4. What does `GET /api/locations/{location_id}/overview` return? Name the main pieces of the overview DTO: location, assigned device counts, and `zones` (thresholds, assigned devices, and those devices’ latest readings, including `tracking_enabled` and `sampling_interval_seconds`), plus strategy key and last recommendation. Why may those reading rows come from the sampler or MQTT ingest, not only from `POST /read`? Why is overview scoped by `location_id`?

> [!NOTE]
> **_Your Answer_**
>
> It returns one `LocationOverviewDto`. Inside it there is the `location` (id and name) and `device_counts`, which counts sensors and actuators but only the ones assigned to a zone in that location. Then there is `zones`, which has every zone of the location with its low and high moisture thresholds, the devices assigned to it, and `latest_readings` for those devices. Each reading has the value, unit and `recorded_at`, and also `tracking_enabled` and `sampling_interval_seconds`, which are copied from the device. At the end there is `strategy_key` and `last_recommendation`, and both are null if no strategy has been saved yet.
>
> The readings can come from the sampler or MQTT because all of those paths go through the same `ReadingIngest` and save the same kind of row into `sensor_readings`. So for the overview it doesn't matter where a reading came from, it just takes the newest one by `recorded_at`. If I only used `POST /read` most of the real data would be missing, since the sampler and MQTT create most of the readings anyway.
>
> It's scoped by `location_id` because that's how the data is organized in this project. Zones belong to a location, devices are assigned using `location_id` and `zone_id`, and the strategy is saved per location too. We don't have any greenhouse id.

5. Why does this phase **not** require a new business table? What already exists from Phases 2–6 that the facade only **composes**?

> [!NOTE]
> **_Your Answer_**
>
> The overview doesn't store anything new, it's just a read view of data we already have. Even the recommendation is calculated again on every request instead of being saved.
>
> Everything it needs was already there from earlier phases: the `devices` table from Phase 2 and 3 (and the zone assignment from Phase 4), `locations` and `zones` from Phase 4, `sensor_readings` and the sampling fields on devices from Phase 5, and `automation_rules` with the evaluate service from Phase 6. The facade just combines these.

6. The overview HTTP handler should call **only** the facade, not reading/strategy/device repositories directly. Why? How does that help tests and later changes to the query shape?

> [!NOTE]
> **_Your Answer_**
>
> The handler should only care about HTTP things, like taking the `location_id` from the path, calling one method and turning `NotFoundError` into a 404. If it called all the repositories itself, the logic for building the overview would be stuck inside the web layer, and I couldn't reuse it or test it without going through HTTP.
>
> Because the handler only uses the facade, I could test `get_overview` with small fake repositories in `test_overview_facade.py`, and then test the real route with the database in a separate test. Also if I change how the queries work later, for example use a SQL view or join devices and readings together, I only need to change the facade or the repositories. The route and the frontend stay the same as long as the DTO doesn't change.

7. The location selector may use the existing locations list. The Overview cards come from **one** overview fetch, and Refresh repeats that same fetch. Why must the React page not stitch device, reading, and automation calls together to build the same snapshot? How does a new reading or a saved strategy show up on overview without extra frontend glue?

> [!NOTE]
> **_Your Answer_**
>
> If the React page did all those calls and merged them, then the rules (which devices are assigned, which reading is the newest, when the recommendation should be null) would be copied into the frontend as well. It would also send many requests, and the answers could come from slightly different moments, so the cards might not even match each other.
>
> In my panel, picking a location calls `fetchOverview(locationId)` once, and the Refresh button just does the same call again. Since the facade reads from the database and runs evaluate every time, a new reading from any source or a newly saved strategy shows up the next time the overview is fetched. I didn't need any extra frontend code for that.

## C. Compare, contrast, and scenarios

8. Contrast Facade with **Adapter**. One makes an existing interface usable; the other makes a subsystem simpler to call. Which is which, and how do both appear in this greenhouse app (Phase 5 vs Phase 7)?

> [!NOTE]
> **_Your Answer_**
>
> Adapter is the one that makes an existing interface usable, it converts something that doesn't fit into the shape our application expects. Facade is the one that makes a subsystem simpler to call. With a facade the interfaces already fit, there are just too many of them to call one by one.
>
> In Phase 5 the sensor adapters (`SimulationSensorAdapter`, `VendorStubSensorAdapter` and `MqttSensorAdapter`) take different payload formats and turn them into one `Reading` behind `SensorPort`. In Phase 7 `LocationOverviewFacade` doesn't translate anything. It calls repositories and the automation service that already use our own types, and then gives back one combined DTO.

9. This phase mentions **N+1** queries. What is an N+1 problem in an overview that lists latest readings for many devices, and what can the facade (or its repository) do about it without putting SQL in the router?

> [!NOTE]
> **_Your Answer_**
>
> N+1 is when you do one query to get a list of N devices and then one more query for each device to get its latest reading. So with 20 devices you end up with 21 queries, and it keeps growing when more devices are added.
>
> I avoided this in the repository layer. `DeviceRepository.list_assigned_devices` gets all the assigned devices of the location in one query, and `ReadingRepository.latest_for_devices` gets the newest reading for all of those ids in one query using `DISTINCT ON (device_id)` ordered by `recorded_at DESC`. After that the facade just groups them by zone in Python. Evaluate still does its own moisture lookup per zone, but I left that inside the strategy service like the requirements said instead of rewriting `decide`.

10. A classmate hides every error behind a generic “overview failed,” so a missing location, a DB outage, and a strategy error look the same. Why is that a trap for a facade?

> [!NOTE]
> **_Your Answer_**
>
> Since the facade sits in front of many subsystems, lots of different errors can pass through it. If all of them become one generic message, the caller can't really react the right way. A missing location should be a 404 so the UI can tell the user to pick another location, but a database outage is a 500 and someone actually needs to fix it. It also makes debugging harder because the real reason is lost.
>
> In my version only `NotFoundError` is turned into a 404. Having no strategy saved isn't treated as an error at all, it just returns 200 with nulls. Other unexpected errors are not caught, so they still show up as real server errors in the logs.
