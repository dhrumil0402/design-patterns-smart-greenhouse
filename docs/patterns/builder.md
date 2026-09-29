# Builder — Location Configuration

## Problem

A location configuration is not one flat record. It's a location plus one or more
zones, and each zone has rules that only make sense together (a low threshold must
be below the high threshold, and both must fall inside the 0.0 to 1.0 VWC range).
If the API just accepted a location name and a list of zone dicts and inserted them
directly, nothing would stop a caller from saving a zone with `low=0.9, high=0.1`,
or a location with zero zones. Validating that shape only inside the FastAPI request
handler puts the rule in the wrong layer. Anything else that constructs a `Location`
later, whether that's a script, a different endpoint, or a test, could bypass it
entirely.

## Solution

`LocationConfigBuilder` (`domain/locations/config_builder.py`) accumulates a location
name and any number of zones through `with_location_name()` and `add_zone()`. Neither
step validates anything. They just store what they're given. All validation happens
once, inside `build()`, which either returns a fully valid, immutable `LocationConfig`
(a frozen dataclass wrapping a frozen `Location` with a tuple of frozen `Zone`s) or
raises `ConfigurationError` before anything touches the database.

Because `Location` and `Zone` are frozen, and `zones` is a tuple rather than a list,
there's no way to end up holding a `LocationConfig` that didn't pass through
`build()`'s checks. The only path to a valid instance is the builder.

## Vs Factory Method / Abstract Factory

Factory Method (Phase 2) answers "which type of a single product should I build?",
like a moisture sensor vs a light sensor, one object per call. Abstract Factory
(Phase 3) answers "which matching family of several products should I build?", like
a simulation kit vs an edge kit, several related objects created together. Builder
answers a different question entirely: "how do I assemble one aggregate that has
multiple required parts and cross-field rules, without letting a half-finished
version leak out?" A location with its zones isn't a "kind" of anything. It's one
object built in steps, and that's why Builder fits here while neither factory
pattern does.

## Where in code

- `domain/locations/entity.py` holds `Zone`, `Location`, and `LocationConfig` (immutable)
- `domain/locations/config_builder.py` holds `LocationConfigBuilder` and the validation rules
- `domain/locations/errors.py` holds `ConfigurationError`
- `application/locations/mappers.py`'s `request_to_config()` calls `.build()` before
  the service ever touches the repository
- `infrastructure/persistence/location_repository.py`'s `save_config()` flushes the
  location first to get its generated id, then commits the location and zones
  together, so a failure rolls back both

## `location_id` naming

The course uses `location_id`, not `greenhouse_id`, throughout: on the `zones`
foreign key, in the API response, and in the TypeScript types. That keeps the schema
and API generic to "a site with zones" rather than assuming greenhouses specifically.

## Extension exercise

Add a `schedule` validation rule that rejects a zone whose `schedule` dict has a
`"watering"` key that isn't a valid `"HH:MM"` 24-hour time string. Where should that
check live, inside `add_zone()` or inside `build()`? Think about whether you want to
reject bad input the moment it's added, or only once the whole config is finalized,
and what that implies if a caller adds a zone and then corrects its schedule before
calling `build()`.