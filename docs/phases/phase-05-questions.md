# Phase 05 - Adapter questions

## A. Pattern

### 1. State the intent of Adapter in plain language. What problem appears when business code speaks a vendor or legacy protocol directly?

Adapter is used when one class or system has an interface that does not match what the application expects. Instead of changing the vendor code or making the whole application understand every different format, the adapter translates it into the format our application already uses.

In this project, a vendor might return nested fields, strange unit names, or timestamps in a different format. If the business code handled those details directly, it would become full of vendor-specific code. Then adding another sensor source would make the application harder to maintain. The adapter keeps those differences in one place and returns a normal `Reading`.

### 2. Name the participants: target / port, adaptee, adapter, and client. What does the adapter translate, and what must it not decide?

The target or port in this phase is `SensorPort`. It defines the reading operation that the application expects.

The adaptee is the thing with the different interface, such as the vendor probe client, the simulation value generator, or an MQTT payload.

The adapters are:

- `SimulationSensorAdapter`
- `VendorStubSensorAdapter`
- `MqttSensorAdapter`

The client is the application service, mainly `ReadingIngest`, because it asks for a reading and does not need to know the exact adapter implementation.

The adapter translates the vendor fields, units, timestamp, and payload shape into the common `Reading` object. It should not decide irrigation rules. For example, it should not decide that the pump must turn on when moisture is below a certain value. That is business logic and belongs in the later Strategy phase.

### 3. GoF distinguishes an object adapter from a class adapter. Which does modern code prefer, and why?

Modern code normally prefers an object adapter that uses composition instead of inheritance.

With composition, the adapter receives or contains the object it needs to translate. This is more flexible because the adapter is not tightly tied to a specific parent class. It also makes testing easier because I can pass in a fake vendor client with a controlled payload.

In this project, the vendor adapter uses a `VendorProbeClient` and translates the result into a `Reading`. It does not need to inherit from the vendor client.

## B. This phase of the application

### 4. What is `SensorPort` in this lab, and what normalized value type do adapters return?

`SensorPort` is the common interface that the application uses to read a sensor. It has a `read(device)` method that returns a normalized `Reading`.

The `Reading` contains:

```text
device_id
value
unit
source
recorded_at
```

The simulation adapter, vendor adapter, and MQTT adapter all produce this same type even though their original data is different.

The application services depend on `SensorPort` instead of directly depending on a simulation driver or vendor SDK because the application should not care where the reading came from. This also means that I can replace one adapter or add another one without rewriting `ReadingIngest`.

### 5. Why is the different raw shape the point of the exercise? How does `source` show which adapter produced the reading, and why must MQTT not open a broker in this phase?

The different raw shapes are the main reason for using Adapter. The simulation adapter creates a value directly, the vendor adapter receives a nested vendor payload, and the MQTT adapter receives a simple dictionary. They are all different inputs, but they are converted into the same `Reading`.

The `source` field shows which adapter produced the reading:

```text
simulation
vendor
mqtt
```

This is useful for seeing where the stored value came from.

The MQTT adapter should not open a broker in this phase because Phase 5 is only testing the translation of the payload. It should accept a dictionary and convert it into a `Reading`. Opening a broker would add an external dependency and make the tests harder to run. The actual HTTP or broker transport is planned for Phase 12, so this phase should keep the adapter focused only on translation.

### 6. Why are readings appended to `sensor_readings` instead of keeping only the latest value? Why do all reading sources share one writer?

Readings are appended because the application needs history. If only the latest value was kept in memory or one database row was overwritten, previous readings would be lost when a new reading arrived or when the application restarted.

The history can be used later by the Strategy phase to evaluate moisture readings, and other later phases can use it for charts, events, and checking how values changed over time.

Manual reads, simulation sampler readings, and future MQTT readings all use one writer, `ReadingIngest.record`, so they follow the same validation and persistence path. This avoids having separate code paths that save readings in different ways.

The sampler skips devices with tracking turned off because the user disabled automatic sampling. It skips MQTT devices because this phase does not poll MQTT devices or connect to a broker. The sensor cards poll the latest stored reading until Phase 12 because WebSocket live updates are not added yet. Polling lets the UI eventually display readings created by the sampler.

### 7. What HTTP status is appropriate when the device is missing versus when the adapter fails?

When the device does not exist, the API should return:

```text
404 Not Found
```

When the adapter cannot read the device or the input is invalid, the API should return a client error such as:

```text
400 Bad Request
```

The router should not see vendor-shaped dictionaries or vendor SDK objects. Those should be translated inside the adapter first. If vendor types reached the router, the API layer would become coupled to the vendor implementation and changing the vendor would affect the HTTP code.

The router should receive the normalized `Reading` or `ReadingDto` instead.

## C. Compare, contrast, and scenarios

### 8. Contrast Adapter with Facade. Give a greenhouse example of each.

Adapter and Facade both hide implementation details, but they solve different problems.

An Adapter changes the shape of an existing interface so that it fits the interface expected by the application. In this phase, `VendorStubSensorAdapter` changes the vendor payload into the common `Reading` format expected through `SensorPort`.

A Facade gives a simpler way to use a group of classes or a whole subsystem. For example, in a later greenhouse phase, a facade could have one method like:

```text
water_zone(zone_id)
```

Internally it could load the zone, check the latest moisture reading, select the actuator, apply the command, and record the action. The facade would simplify using several services, while the adapter mainly converts one interface into another.

### 9. Contrast Adapter with Decorator. What is different about the interface they present to the client?

An Adapter changes the interface so an incompatible object can be used by the client. The client sees the interface it already expects, such as `SensorPort`.

A Decorator keeps the same interface but adds extra behavior around the original object. For example, a decorator around `ActuatorPort` could add logging, safety checks, or metrics and still expose:

```python
apply(device_id, command, payload)
```

So the main difference is that Adapter makes something compatible, while Decorator adds behavior without changing the interface expected by the client.

### 10. Why is irrigation policy inside the vendor adapter a trap?

Putting irrigation policy inside the vendor adapter mixes two different responsibilities. The adapter should only translate the vendor data into a normalized `Reading`.

If the adapter contains a rule like:

```text
if moisture < 0.3 then water
```

then irrigation behavior becomes tied to that particular vendor adapter. The simulation adapter or MQTT adapter might not follow the same rule, which would make the system inconsistent.

That decision should be made later by the Strategy implementation. Strategy can evaluate the normalized moisture reading together with the zone thresholds and then decide whether watering is needed.

The adapter should stay responsible for:

- Reading or receiving the external data.
- Translating fields and units.
- Converting the timestamp.
- Setting the correct source.
- Returning a normalized `Reading`.

It should not make irrigation decisions.
