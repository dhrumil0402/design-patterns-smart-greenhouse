## A. Pattern

1. State the intent of Abstract Factory in plain language. What goes wrong when related products are chosen independently (`if format` for each piece) instead of as a **family**?

> [!NOTE]
> ***Your Answer***
>
>  Builder lets you assemble a complex object step by step and only validate it at the end, instead of jamming everything into one big constructor. A location config has a name and multiple zones with their own rules, so a single constructor call or a half filled dict could easily produce something invalid.

2. Name the main participants (**abstract factory**, **concrete factory**, **abstract products**, **concrete products**, **client**). How does choosing a factory at the start **commit** the client to one family?

> [!NOTE]
> ***Your Answer***
>
>Product is `LocationConfig`. Builder is `LocationConfigBuilder`. No director was needed here since the steps are simple. Client is `request_to_config()`, which drives the builder. Before `build()` succeeds, what you hold is just builder state, not a trustworthy domain object.

3. When should you use Abstract Factory, and when should you skip it (for example only one product type per request, or mixing siblings is valid)?

> [!NOTE]
> ***Your Answer***
>
> `build()` rejects: empty location name, zero zones, and low threshold not strictly less than high threshold (plus thresholds outside 0.0 to 1.0). These live in the domain, not just HTTP, because any other caller besides the API could construct a `Location` and skip validation if the rule only sat in FastAPI.
>

## B. This phase of the application

4. In this lab, what is a **device family**, and what does `create_device_set()` (or your equivalent) return? Why must a simulation kit and an edge kit not mix incompatible siblings?

> [!NOTE]
> ***Your Answer***
>
> The builder produces one location plus its zones together. We use `location_id` instead of `greenhouse_id` so the schema stays generic to "a site with zones" rather than assuming a greenhouse specifically.

5. Phase 2 Factory Method creators still exist. How does Abstract Factory **compose** them rather than replace them? What would you lose if you deleted the sensor creators and inlined all construction inside the family factory?

> [!NOTE]
> ***Your Answer***
>
> DTO comes in, mapper calls the builder step by step, `build()` runs last. If it raises `ConfigurationError`, nothing gets saved, not even the location. Assignment waits for the zone to exist because a device needs a real `zone_id` to point at. Client only sends `zone_id`, not `location_id`, so the two can never disagree.

6. Why add a `device_family` column on the existing `devices` table (with a default/backfill such as `"simulation"`) instead of a new table per family? What happens to Phase 2 sensor rows if you forget the backfill?

> [!NOTE]
> ***Your Answer***
>
> One transaction matters because if the location commits and the zone insert fails after, you get a location with no zones, exactly the half built state Builder is meant to prevent. We flush the location first to get its id, then commit location and zones together so a failure rolls back both.

7. `POST /api/devices/provision` returns a kit (expected size: two sensors and two actuators). `GET /api/devices` can filter by `family` and `role`. Why must the UI be able to filter by family? Why do `/api/sensors` routes from Phase 2 still need to work?

> [!NOTE]
> ***Your Answer***
>
> The wizard just collects input across steps and sends it all on submit. It does a quick client side check for fast feedback, but the backend builder is the real gatekeeper since the frontend check can drift or be bypassed.

## C. Compare, contrast, and scenarios

8. Draw the contrast in one paragraph: Factory Method vs Abstract Factory. Use the questions “which **one** product?” versus “which product **line**?” and mention that Abstract Factory often **uses** Factory Method–style methods inside.

> [!NOTE]
> ***Your Answer***
>
> Factory Method picks one product type. Abstract Factory picks a whole matching family. Builder assembles one valid object out of several parts with rules between them. A location with zones is not a type or a family, it is one thing built in steps and checked once at the end.

9. A DTO or HTTP handler constructs concrete simulation/edge device types directly, bypassing the family factory. What consistency bug can that reintroduce? How should HTTP stay on the abstract factory / service instead?

> [!NOTE]
> ***Your Answer***
>
> Fluent chaining (`self` returns) is just a style choice for how the calls read. Builder is about deferring validation to one `build()` step. You can have one without the other, chaining with no real pattern, or the pattern with no chaining.

10. Someone proposes a single “god factory” that creates locations, readings, and devices “because we already have a factory.” Why is that a misuse of Abstract Factory?

> [!NOTE]
> ***Your Answer***
>
> Validating only in FastAPI and leaving `build()` empty means anything else that builds a `Location`, like a script or another endpoint, has no protection. Mutating a builder's output after `build()` and still trusting it breaks the whole guarantee Builder gives you. Our frozen dataclasses and tuple `zones` make that second mistake impossible here, but the lesson is that a "finished" product should stay finished.