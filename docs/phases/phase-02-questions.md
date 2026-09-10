Phase 2 — Factory Method questions
A. Pattern

1. Intent of Factory Method, and the problem with scattered constructors

Factory Method is about letting a separate class decide which concrete object to create, instead of the calling code deciding that itself. The caller just asks for "a moisture sensor" or "a light sensor" through a shared interface, and doesn't need to know the actual class being built. The problem that shows up without this is that if every place that needs to create a sensor writes its own if type == "moisture": ... elif type == "light": ... block, you end up with that same logic copy pasted in multiple places (the API handler, tests, maybe a seed script), and if you add a third sensor type later you have to remember to update every single one of those blocks. It's easy to miss one and get inconsistent behavior.

2. Main participants

Product is the thing actually being created. In general terms this is the shared type/interface all the concrete products share.
Concrete product is one specific variant of that thing.
Creator is the class that declares the factory method, usually as an abstract method other classes have to implement.
Concrete creator overrides that factory method to actually build one specific concrete product.
Client is whoever is using the creator, it just calls the factory method and doesn't care which concrete product comes back.

3. Adding a new variant: polymorphic creators vs one big if/elif

With polymorphic creators, adding a new variant means adding a new class that implements the creator interface, plus one line in the registry that maps a key to that new class. Nothing that already exists has to be touched or re-tested. With a single shared if/elif function, adding a new variant means editing that function directly, adding another branch, which means you're modifying code that already works and already has other branches in it, so there's more risk of breaking an existing case by accident. This matters for extension because polymorphic creators follow the idea of being open for extension but closed for modification, you extend by adding, not by editing.

B. This phase of the application

4. Product and concrete creators in this app, why go through a creator

The product here is the Sensor entity (the plain domain object with device_type, display_name, and default_config). The concrete creators are MoistureSensorCreator and LightSensorCreator, both implementing the same SensorCreator interface with a create_sensor method. The API handler (through the sensor service) has to go through get_creator(type) instead of constructing a sensor directly because that's the only way the code stays extendable. If the router directly did something like if type == "moisture": Sensor(device_type="moisture_sensor", ...), then every new sensor type would mean editing the router itself, which mixes creation logic into the HTTP layer where it doesn't belong. Going through the registry keeps that decision entirely in the domain layer.

5. Why type and device_type are different fields, who decides them

type is just the short key the client sends to say which kind of sensor they want, like "moisture" or "light". device_type is the actual stored value in the database, like "moisture_sensor", and it's decided by the concrete creator itself, not by the client. The reason they're different is that the client shouldn't need to know or send the exact internal naming convention used in storage, it just needs to pick a type key from a small known set. The creator is the one place that decides both the stored device_type string and the default_config values, so if that internal naming or those defaults ever need to change, it only changes in one spot (the creator class) and the API contract for clients doesn't have to change at all.

6. Single devices table with role="sensor" instead of a separate sensors table

Using one devices table with a role column instead of a dedicated sensors table means the same table can later hold other kinds of devices too, like actuators, just by giving those rows a different role (for example role="actuator"). This is setting up for Phase 3, which adds actuators and a device_family concept. If sensors had their own separate table, adding actuators later would either mean a whole new table with duplicated structure, or a bigger migration to merge things together. Keeping everything in devices from the start avoids that.

7. Handling an unknown type

If the client posts an unknown type, it should be rejected with a 400 and a useful error message, and that rejection should happen in the registry/service layer, not by having the router fall back to constructing some concrete class anyway. In my implementation, get_creator raises a ValueError if the type isn't in the registry, and the router catches that and turns it into an HTTPException with status 400. This way an invalid type never even gets close to the database, it fails before anything is created or inserted.

C. Compare, contrast, and scenarios

8. Factory Method vs simple factory

A simple factory is one function with a big if/elif inside it that returns different objects based on the input. It's good enough when there are only a couple of variants and they're unlikely to grow much, since it's less code to set up than a bunch of separate creator classes. This phase still wants polymorphic creators because sensor types are expected to keep growing (the extension exercise literally adds a temperature sensor), and because each creator can hold its own more complex creation logic if needed later without cluttering one shared function. It also matches the class based structure the rest of the project uses (repository, service, etc), so it's more consistent with the whole architecture, not just this one piece.

9. Factory Method vs Abstract Factory

Factory Method answers "which single product should be created" based on a type key. Abstract Factory answers a different question, which is "which whole family or bundle of related products should be created together." Factory Method is enough for Phase 2 because sensors are being created one at a time, independently of each other. Phase 3 needs Abstract Factory because it's creating a device_family, meaning a bundle of related devices (probably a sensor plus matching actuators) that need to be created together as a consistent set, not just one object at a time.

10. SQLAlchemy commits or FastAPI parsing inside a creator

That's a trap because it breaks the whole point of keeping the domain layer separate from infrastructure and the API layer. If a creator started doing session commits, it would mean the domain code depends on SQLAlchemy, and you couldn't test creator logic anymore without an actual database connection, which defeats the point of my creator unit tests running without a DB. Same thing with FastAPI request parsing, that's an HTTP concern and has nothing to do with deciding what a sensor's defaults should be. Persistence should stay in the repository, and HTTP parsing should stay in the router. The creator's only job is to build a Sensor object in memory, nothing else.