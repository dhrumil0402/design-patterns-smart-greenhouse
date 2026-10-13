# Phase 06 - Strategy questions

## A. Pattern

### 1. State the intent of Strategy in plain language. How does the context use a strategy, and why must "choose which algorithm" stay separate from "run the algorithm"?

Strategy lets me put several ways of doing the same job behind one interface, so the code that needs a decision does not care which algorithm gives it. In this project the job is deciding whether a zone needs irrigation.

`AutomationService` is the context. It builds a plain `LocationAutomationContext` for each zone and calls `strategy.decide(context)`. It does not know if the strategy is conservative or aggressive.

Choosing the algorithm (`get_strategy(key)` with the saved `strategy_key`) is separate from running it (`decide`). Because of that, adding a new policy does not change the code that runs it, and an unknown key is rejected before any decision logic starts.

### 2. Name the participants (strategy, concrete strategies, context, client). What goes wrong when all policies live as `if/elif` inside the context (or inside an HTTP router)?

- **Strategy:** the `AutomationStrategy` interface with `decide(context)`.
- **Concrete strategies:** `ConservativeMoistureStrategy` and `AggressiveMoistureStrategy`.
- **Context:** `AutomationService`. It gathers the data and passes the decision to the strategy.
- **Client:** the operator or API call that chooses and saves the key (`PUT /api/locations/{location_id}/automation`).

If all the policies were `if/elif` inside the service or the router, every new policy would mean editing that same file, and it would keep growing. The policies would also be harder to unit test, because I would need HTTP or a database just to test one rule. The HTTP layer would end up holding irrigation rules, which do not belong there.

### 3. When should you use Strategy, and when should you skip it (one algorithm only; or the variation is a lifecycle mode rather than a chosen policy)?

Strategy is useful when there are several ways to do the same job and someone chooses one of them, for example by saving a setting. Irrigation is a good example, because different growers want different policies.

I should skip it when there is only one algorithm, because the interface would only add extra classes with no benefit.

I should also skip it when the variation is a lifecycle mode. In that case the behaviour changes because of what happened to the object, for example a pump going from idle to running. That is State, not a policy that someone selects.

## B. This phase of the application

### 4. In this lab, what does a strategy's `decide(context)` return (action + reason)? Give a concrete difference you implemented between conservative and aggressive on the same moisture reading and zone thresholds.

`decide(context)` returns a `Recommendation` with an `action` (`irrigate` or `wait`) and a `reason` string. It also has an optional `score`, but my two strategies do not use it yet.

The two strategies use different trigger levels:

```text
conservative: irrigate when moisture < low threshold
aggressive:   irrigate when moisture < (low + high) / 2
```

In my test run, Bench 1 had a band of 0.20 to 0.45, so the midpoint was 0.325. With a reading of about 0.31, conservative returned `wait` because 0.31 is not below 0.20. Aggressive returned `irrigate` because 0.31 is below 0.325. So the same reading and the same thresholds gave different advice.

### 5. Where do the numbers in `LocationAutomationContext` come from? Why does this phase not add a scheduler or a broker? Why must strategies receive a plain context object? Why are thresholds read from zones?

The numbers come from the database. The thresholds come from the zone's row in `zones`. The moisture is the latest `sensor_readings` row among moisture sensors whose `devices.zone_id` is that zone. The repository returns these as plain values, and `AutomationService` builds the context from them.

This phase does not add a scheduler or a broker because readings already arrive through the Phase 5 path (manual read, simulation sampler, or translated MQTT payload). Strategy only has to read whatever is latest, so it does not need to know how the reading got there.

Strategies receive a plain context object so they stay pure Python. They can be tested with a fake context, and they do not depend on SQLAlchemy or FastAPI.

Thresholds come from `zones` because each zone has its own settings. For example, Bench 1 and Bench 2 have different bands. If I hardcoded numbers in the strategy class, the user's configuration would be ignored.

### 6. Why must `POST .../automation/evaluate` use the saved key rather than a key the client sends only in that request? What happens on the next evaluate after the operator changes strategy but moisture stays the same?

The saved key is what the operator chose for that location, so it should be the single source of truth. It is stored in `automation_rules`, with one row per `location_id`.

If evaluate trusted a key sent in the request, different clients could get different answers for the same location, and saving a strategy would not mean anything.

After the operator changes the strategy, the next evaluate reads the new saved key. The recommendation can change even if the moisture stays the same. For example, at about 0.31 with a band of 0.20 to 0.45, switching from conservative to aggressive changes `wait` into `irrigate`.

### 7. Strategy recommends (irrigate / wait). Why keep `decide` separate from execute? Which later pattern is meant to carry out the action?

A strategy should only decide. Carrying out the action is a separate step.

Keeping them separate means the decision logic can be tested without hardware, and the result can be shown to the user as a recommendation first. If a strategy started the pump itself, then pressing Evaluate or running a test could turn on real equipment, and the algorithm would be tied to the actuator.

The pattern that carries out the action is Command (Phase 10). A command represents "run this action", so it can be logged and checked before it uses the actuator port from Phase 5.

## C. Compare, contrast, and scenarios

### 8. Contrast Strategy with State (Phase 8). Who typically changes the active object, and is the variation a policy or a lifecycle?

Strategy and State both delegate work to an object with the same interface, but the reason the object changes is different.

In Strategy, the client or operator picks the object, for example by saving `conservative` or `aggressive` for a location. The variation is a policy, which means different ways of doing the same job.

In State, the object changes because of events during its life, for example a device going from idle to running to faulted. The variation is a lifecycle. Also, strategies normally do not know about each other, but states often know which state can come next.

### 9. Contrast Strategy with Adapter (Phase 5) and with Builder (Phase 4). Which one translates a foreign API, which one assembles a valid aggregate, and which one swaps an algorithm?

- **Adapter (Phase 5)** translates a foreign interface into the one the application expects. For example, `VendorStubSensorAdapter` turns a vendor payload into a normal `Reading`.
- **Builder (Phase 4)** assembles a valid aggregate step by step. For example, `LocationConfigBuilder` builds a location with its zones and validates it in `build()`.
- **Strategy (Phase 6)** swaps an algorithm behind one interface, such as conservative or aggressive irrigation.

So Adapter translates, Builder assembles, and Strategy swaps the decision logic.

### 10. A classmate writes one "mega-strategy" with `if conservative` / `if aggressive` inside one class. Another strategy class calls the actuator adapter to water immediately. Explain why each is a trap.

A mega-strategy only moves the `if/elif` problem into one class. A third policy still means editing that class, and I lose the main benefit of Strategy, which is small separate classes behind one interface that can be tested on their own.

A strategy that calls the actuator adapter mixes deciding with doing. Evaluating would then have a side effect, so just pressing Evaluate or running a test could start a pump. It would also tie the algorithm to hardware, so it could not be tested with a fake context.

A strategy should only return a recommendation, and executing it should be a separate step.
