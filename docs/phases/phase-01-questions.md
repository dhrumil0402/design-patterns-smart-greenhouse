## A. Pattern

1. In your own words, what is a design pattern? What is it *not*?

A design pattern is a common way to solve a problem that keeps coming up when you're designing software. It's not actual code you can just copy in, it's more like an idea or a template for how to structure things, and you still have to write it yourself depending on your situation. It's also not a library, and it's not something you're required to use everywhere. It's just a tool you pick up when it actually fits what you're doing.

2. Name the three GoF pattern families. For each family, give one-sentence: what kind of design problem it addresses. Then place **Factory Method** and **Strategy** into the correct family.

The three families are:

    Creational patterns deal with how objects get created so your code isn't stuck depending on one specific class.
    Structural patterns are about how you combine classes and objects into bigger structures without making everything tightly locked together.
    Behavioral patterns are about how objects communicate and how the responsibility for doing something gets split up between them.

Factory Method is Creational because it's about how an object gets created, letting a subclass decide what to build.

Strategy is Behavioral because it's about being able to swap out an algorithm or behavior while the program is running, without changing the class using it.

3. A teammate wants to add a pattern “because it is on the course list,” even though the feature is small and unlikely to grow. When should you **skip** a pattern? What risk do you take if you apply one too early?

Skip a pattern when the feature is small and there's really only one reasonable way to build it, and it doesn't seem like it's going to need different versions later. Using a pattern anyway just adds more files and more indirection for something that never needed to be flexible. If you apply a pattern too early, you risk over engineering it. The code gets harder to follow because there's extra structure in the way, and a lot of the time you end up guessing wrong about what actually needs to change later since you haven't seen the real requirements yet.

## B. This phase of the application

4. Why does Phase 1 ship a vertical slice that does almost no greenhouse business logic? What does “empty but running” prove that a folder of unimplemented classes would not?

Because this phase isn't really about the greenhouse features at all, it's about proving all the pieces can actually talk to each other. The backend needs to be able to reach Postgres, the frontend needs to be able to reach the backend, and the migrations need to actually run. If I just had empty folders with a bunch of stub classes, none of that would be proven yet. Having something small but fully working end to end, even if it's just a health check, catches the annoying wiring bugs like wrong ports or missing env vars before there's real feature code sitting on top of it.

5. List the four backend layer packages used in this course (`domain`, `application`, `infrastructure`, `interfaces/api`). For each, state what belongs there and give one example of something that must **not** live in `domain`.

The four backend layers, what goes where, and what shouldn't be in domain

**domain** is supposed to hold the core business entities and rules. Right now it's empty since we don't have any greenhouse entities yet, that's coming in Phase 2 with devices. Something that should not be in here is FastAPI routes or SQLAlchemy models, domain shouldn't care that it's being served over HTTP or saved into Postgres.
**application** is where the use cases go, basically the steps for doing an actual business action. Also empty right now.
**infrastructure** is where I put settings.py for loading env vars and db.py for the SQLAlchemy engine and the SELECT 1 check. This layer handles the technical stuff.
**interfaces/api** is the actual FastAPI routes, like health.py. This is the layer that talks HTTP.

6. What does `GET /health` return, and why does it check the database instead of only reporting that the HTTP process is up? Why is API documentation served at `/scalar`, and why is `/docs` disabled?

It returns something like **{"status": "ok", "db": "ok"}**. It checks the database instead of just saying the server is up because the process being alive doesn't actually tell you if the app works. If Postgres was down, the API would still respond to requests, just with errors, so the health check needs to actually test the database connection to mean anything. Docs are served at /scalar because that's what this course wants us to use, and /docs is turned off on purpose so there's only one documented API reference instead of two different ones.

7. Phase 1 requires Alembic (or equivalent) with a **baseline** migration and **no** business tables such as `devices`. Why introduce the migration toolchain before any product schema? What would go wrong if you created tables by hand in Postgres and only added migrations later?

The point is to prove the migration tool actually works while there's nothing important riding on it yet, no real data and no real tables. If I made tables by hand in Postgres first and added Alembic later, Alembic wouldn't know those tables already exist, so I'd have to fake a migration to match what's already there or things would get out of sync between what the database actually has and what the migration history claims it should have. Setting the baseline now means every table from here on has to go through a migration, so there's a clean history of the schema from the start.

## C. Compare, contrast, and scenarios

8. Explain **dependency direction** in this skeleton: which layers may import which? Why must domain code not import FastAPI, SQLAlchemy, or Pydantic models used as HTTP schemas?

The outer layers are supposed to depend on the inner ones, not the other way around. interfaces/api depends on application, application depends on domain, but domain doesn't depend on either of them. Infrastructure gets used by the outer layers to actually do things like connect to the database. Domain shouldn't import FastAPI or SQLAlchemy because those are implementation details about how the app is served or how data gets stored. If domain code depended on FastAPI, it would be a lot harder to test the business logic without running an actual web server, and you couldn't reuse that logic anywhere else without dragging FastAPI along with it.

9. The frontend cannot show a healthy badge. A classmate blames “the patterns.” What should you check first (stack, CORS/proxy, health JSON), and why is that a Phase 1 concern rather than a later pattern concern?

Since Phase 1 doesn't actually use any patterns, that's not where the problem would be. First things I'd check are whether the backend is actually running, whether Postgres is running, whether CORS_ORIGINS in the backend's .env actually matches the frontend's URL and whether I restarted uvicorn after changing it since env changes don't hot reload, whether VITE_API_BASE_URL in the frontend points at the right backend address, and whether hitting /health directly in the browser actually returns the JSON I expect. This is a Phase 1 problem because it's just about the stack being wired up correctly, ports, CORS, env variables, none of that has anything to do with a design pattern.

10. Course completion is at **Phase 12**, not Phase 1. What is still missing after a successful skeleton, and how do later phases add behaviour without rewriting the foundations you laid here?

After Phase 1 there's still no real business logic, no actual entities like a device, nothing being stored, and no pattern has actually been used yet, this phase was only about getting the skeleton running. Later phases can build on top of it without redoing everything because the layer structure and the Alembic setup are already there. Phase 2 just adds a new migration on top of the baseline one, adds real domain entities, and adds new routes, instead of having to restructure the whole project again.