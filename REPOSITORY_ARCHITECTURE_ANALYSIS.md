# Repository Architecture Analysis — `END-i/gate-control`

## Scope

This document summarizes the overall repository architecture, directory structure, backend/frontend split, infrastructure and deployment assets, tests, scripts, configuration layout, structural risks, and recommended improvements for long-term maintainability.

## 1. Top-Level Layout

The repository is organized as a monorepo with separate backend and frontend applications, plus shared operational assets at the root:

- `backend/` — FastAPI application, database models, schemas, migrations, and tests. (`/home/runner/work/gate-control/gate-control/backend/main.py:1`, `/home/runner/work/gate-control/gate-control/backend/api/router.py:1`)
- `frontend/` — SvelteKit application with shared UI code, routes, and tests. (`/home/runner/work/gate-control/gate-control/frontend/src/routes/+layout.svelte:1`, `/home/runner/work/gate-control/gate-control/frontend/src/lib/api.ts:1`)
- `scripts/` — local automation, smoke checks, coverage, backup/restore, and helper scripts. (`/home/runner/work/gate-control/gate-control/scripts/check-all.sh:1`)
- `docs/` — architecture, governance, API contract, runbooks, release notes, and project structure references. (`/home/runner/work/gate-control/gate-control/docs/architecture.md:1`, `/home/runner/work/gate-control/gate-control/docs/project-structure-reference.md:1`)
- `docker-compose.yml` — root-level multi-service local orchestration. (`/home/runner/work/gate-control/gate-control/docker-compose.yml:1`)
- `.env.example` / `.env.ci` — environment templates for local and CI usage. (`/home/runner/work/gate-control/gate-control/.env.example:1`, `/home/runner/work/gate-control/gate-control/.env.ci:1`)
- `package.json` — root entrypoint for backend/frontend/dev automation. (`/home/runner/work/gate-control/gate-control/package.json:1`)
- `simulator.py` — standalone webhook/camera event emulator. (`/home/runner/work/gate-control/gate-control/simulator.py:1`)

This is effectively a full-stack product repository rather than a library repository.

## 2. Architectural Style

The project uses a layered, full-stack application architecture with a backend-for-frontend pattern:

- The **backend** exposes REST endpoints and SSE streams for the frontend and also accepts external camera webhook events. (`/home/runner/work/gate-control/gate-control/backend/api/router.py:11`, `/home/runner/work/gate-control/gate-control/backend/api/logs.py:73`)
- The **frontend** consumes backend APIs through a centralized client wrapper. (`/home/runner/work/gate-control/gate-control/frontend/src/lib/api.ts:11`)
- The **camera / hardware integration** enters through `/api/webhook/anpr`, and gate actuation is deferred into a relay-job queue processed by an async worker. (`/home/runner/work/gate-control/gate-control/backend/api/webhook.py:103`, `/home/runner/work/gate-control/gate-control/backend/core/relay_worker.py:13`)

On the backend, the intended layering is:

1. **HTTP/API layer** — `backend/api/`
2. **Infrastructure and shared runtime layer** — `backend/core/`
3. **Persistence access layer** — `backend/crud/`
4. **Persistence model layer** — `backend/models/`
5. **External API schema layer** — `backend/schemas/`

Representative examples:

- `api/vehicles.py` calls `crud.vehicle` and uses `schemas.vehicle` and `models.admin`. (`/home/runner/work/gate-control/gate-control/backend/api/vehicles.py:8`, `/home/runner/work/gate-control/gate-control/backend/api/vehicles.py:17`)
- `api/stats.py` delegates to `crud.stats`. (`/home/runner/work/gate-control/gate-control/backend/api/stats.py:6`)
- `core/database.py` wires SQLAlchemy engine/session setup and registers models. (`/home/runner/work/gate-control/gate-control/backend/core/database.py:3`)

## 3. Backend Structure

### 3.1 Application composition

`backend/main.py` is the composition root:

- configures logging (`configure_logging`)
- validates runtime secrets
- initializes the DB and seeds the first admin
- starts background tasks for cleanup and relay processing
- mounts `/media`
- installs CORS and security middleware
- exposes `/health` and `/metrics`

See `/home/runner/work/gate-control/gate-control/backend/main.py:18`, `/home/runner/work/gate-control/gate-control/backend/main.py:48`, `/home/runner/work/gate-control/gate-control/backend/main.py:80`, `/home/runner/work/gate-control/gate-control/backend/main.py:112`, `/home/runner/work/gate-control/gate-control/backend/main.py:128`, `/home/runner/work/gate-control/gate-control/backend/main.py:156`.

### 3.2 API layer

`backend/api/router.py` aggregates domain routers under `/api`. (`/home/runner/work/gate-control/gate-control/backend/api/router.py:11`)

Routers are separated by capability:

- `auth.py`
- `logs.py`
- `relay.py`
- `stats.py`
- `system.py`
- `vehicles.py`
- `webhook.py`

This is a good domain-oriented API split. (`/home/runner/work/gate-control/gate-control/backend/api/router.py:3`)

### 3.3 Core runtime layer

`backend/core/` currently contains:

- settings/config (`config.py`)
- database bootstrapping (`database.py`)
- dependency/auth helpers (`dependencies.py`)
- relay hardware adapter (`hardware.py`)
- rate limiting (`rate_limit.py`)
- relay worker (`relay_worker.py`)
- retention cleanup (`cleanup.py`)
- secrets prefetch (`secrets.py`)
- storage abstraction (`storage.py`)
- logging (`logging_config.py`)
- bootstrap seeding (`seed.py`)
- system status tracking (`system_status.py`)

References: `/home/runner/work/gate-control/gate-control/backend/core/config.py:12`, `/home/runner/work/gate-control/gate-control/backend/core/database.py:14`, `/home/runner/work/gate-control/gate-control/backend/core/hardware.py:6`, `/home/runner/work/gate-control/gate-control/backend/core/rate_limit.py:159`, `/home/runner/work/gate-control/gate-control/backend/core/storage.py:41`.

### 3.4 CRUD layer

`backend/crud/` encapsulates database operations by entity or use case. This is a positive separation from HTTP handlers, but the organization is slightly inconsistent:

- `crud/access_log.py` handles writes for logs. (`/home/runner/work/gate-control/gate-control/backend/crud/access_log.py:8`)
- `crud/logs.py` handles log reads/queries, splitting one domain across two files. (`/home/runner/work/gate-control/gate-control/backend/api/logs.py:16`)

### 3.5 Models and schemas

- `backend/models/` contains ORM definitions and enums. (`/home/runner/work/gate-control/gate-control/backend/models/relay_job.py:13`)
- `backend/schemas/` contains API-facing request/response contracts. (`/home/runner/work/gate-control/gate-control/backend/api/vehicles.py:17`)

This is a standard and maintainable split.

### 3.6 Background work

The system uses in-process async loops for operational work:

- `run_cleanup_service()` (`/home/runner/work/gate-control/gate-control/backend/core/cleanup.py:73`)
- `run_relay_worker()` (`/home/runner/work/gate-control/gate-control/backend/core/relay_worker.py:13`)

These are launched directly from the FastAPI lifespan hook. (`/home/runner/work/gate-control/gate-control/backend/main.py:80`)

## 4. Frontend Structure

The frontend is a SvelteKit app with a small shared library and route-based pages.

### 4.1 Shared library

`frontend/src/lib/` contains:

- `api.ts` — API wrapper and auth token injection. (`/home/runner/work/gate-control/gate-control/frontend/src/lib/api.ts:11`)
- `stores/auth.ts` — auth state store. (`/home/runner/work/gate-control/gate-control/frontend/src/lib/api.ts:3`)
- `components/` — shared UI pieces such as vehicle form, language switcher, system status indicator, image modal.
- `i18n.ts` — localization bootstrap.

### 4.2 Routes

`frontend/src/routes/` contains route-level screens:

- `+layout.svelte` — authenticated app shell/navigation/manual trigger. (`/home/runner/work/gate-control/gate-control/frontend/src/routes/+layout.svelte:18`)
- `+page.svelte` — dashboard. (`/home/runner/work/gate-control/gate-control/frontend/src/routes/+page.svelte:1`)
- `login/+page.svelte`
- `logs/+page.svelte`
- `vehicles/+page.svelte`

This is a clean page-level split.

### 4.3 Frontend/backend contract shape

The frontend depends directly on backend REST endpoints via a single base URL environment variable. (`/home/runner/work/gate-control/gate-control/frontend/src/lib/api.ts:5`)

That is simple, but types are locally duplicated inside route files rather than generated from the backend schema. (`/home/runner/work/gate-control/gate-control/frontend/src/routes/+page.svelte:7`, `/home/runner/work/gate-control/gate-control/frontend/src/routes/vehicles/+page.svelte:8`)

## 5. Infrastructure, Deployment, and Configuration

### 5.1 Docker and Compose

The root `docker-compose.yml` defines:

- `postgres`
- `backend`
- `frontend`
- optional `minio` via profile `s3`

This provides a straightforward local stack with optional object storage. (`/home/runner/work/gate-control/gate-control/docker-compose.yml:1`, `/home/runner/work/gate-control/gate-control/docker-compose.yml:47`)

The backend and frontend each have their own Dockerfile:

- backend: Python 3.11 + `uvicorn` (`/home/runner/work/gate-control/gate-control/backend/Dockerfile:1`)
- frontend: multi-stage Node 22 build/runtime (`/home/runner/work/gate-control/gate-control/frontend/Dockerfile:1`)

### 5.2 Configuration organization

Configuration is mostly environment-driven:

- typed backend settings in `backend/core/config.py` (`/home/runner/work/gate-control/gate-control/backend/core/config.py:12`)
- sample values in `.env.example` (`/home/runner/work/gate-control/gate-control/.env.example:1`)
- CI-specific values in `.env.ci` (`/home/runner/work/gate-control/gate-control/.env.ci:1`)

Settings include application, auth, relay, webhook, rate-limit, Redis, Vault, metrics, and media-storage concerns in a single `Settings` model. (`/home/runner/work/gate-control/gate-control/backend/core/config.py:19`)

### 5.3 CI/CD

The repository includes multiple workflow files:

- `ci.yml`
- `release.yml`
- `versioning.yml`
- `nightly.yml`
- `backup-restore-drill.yml`

These are housed cleanly under `.github/workflows/`.

## 6. Tests and Validation Organization

### 6.1 Backend tests

Backend tests are centralized under `backend/tests/`, with a shared `conftest.py` and focused files for auth, migrations, security, relay queue, webhook logic, storage retention, etc. (`/home/runner/work/gate-control/gate-control/backend/tests/conftest.py:1`)

This is a strong structure overall.

### 6.2 Frontend tests

Frontend tests are split across:

- `frontend/src/tests/` for unit tests (`/home/runner/work/gate-control/gate-control/frontend/src/tests/LanguageSwitcher.test.ts:1`)
- `frontend/tests/e2e/` for Playwright tests (`/home/runner/work/gate-control/gate-control/frontend/tests/e2e/auth.spec.ts:1`)

This works, but the split is slightly awkward because unit tests live under `src/tests` while e2e tests live under `tests/e2e`.

### 6.3 Scripted validation

`scripts/check-all.sh` acts as a broad local quality gate:

- backend lint
- backend typecheck
- backend tests
- frontend install
- frontend lint/check
- frontend tests
- Docker builds

See `/home/runner/work/gate-control/gate-control/scripts/check-all.sh:43`.

## 7. Structural Anti-Patterns and Risks

### 7.1 `backend/core/` is a catch-all bucket

`backend/core/` mixes:

- configuration
- DB setup
- auth dependencies
- external integrations
- background workers
- cleanup jobs
- storage abstraction
- operational state

This weakens boundaries and makes the directory an unscoped dumping ground as the system grows. Evidence: `/home/runner/work/gate-control/gate-control/backend/core/config.py:12`, `/home/runner/work/gate-control/gate-control/backend/core/hardware.py:6`, `/home/runner/work/gate-control/gate-control/backend/core/relay_worker.py:13`, `/home/runner/work/gate-control/gate-control/backend/core/storage.py:41`.

### 7.2 Complex business logic lives in HTTP route modules

`backend/api/webhook.py` contains a large amount of domain logic directly in the route module:

- auth verification helpers
- payload normalization
- idempotency handling
- image saving
- access decision logic
- access-log creation
- relay-job creation
- audit event creation

See `/home/runner/work/gate-control/gate-control/backend/api/webhook.py:33`, `/home/runner/work/gate-control/gate-control/backend/api/webhook.py:83`, `/home/runner/work/gate-control/gate-control/backend/api/webhook.py:103`.

This creates a fat controller and makes the business flow harder to test independently of HTTP.

### 7.3 In-process workers are tightly coupled to web app lifecycle

`main.py` starts cleanup and relay workers in the same process as the web app. (`/home/runner/work/gate-control/gate-control/backend/main.py:90`)

That is acceptable for a small deployment, but it couples:

- request-serving lifecycle
- worker lifecycle
- scaling behavior
- fault isolation

If the system grows, these concerns should be separable.

### 7.4 Operational state is stored only in memory

`core/system_status.py` stores last webhook receipt in a module global. (`/home/runner/work/gate-control/gate-control/backend/core/system_status.py:5`)

This is not reliable across multiple processes or replicas and creates environment-sensitive behavior.

### 7.5 Environment-specific behavior is embedded in application startup

Examples:

- startup schema creation varies by `APP_ENV` / `AUTO_CREATE_SCHEMA` in `core/database.py`. (`/home/runner/work/gate-control/gate-control/backend/core/database.py:24`)
- startup secret enforcement varies by `APP_ENV` in `main.py`. (`/home/runner/work/gate-control/gate-control/backend/main.py:48`)
- Vault prefetch is executed at import time before settings loading. (`/home/runner/work/gate-control/gate-control/backend/main.py:26`, `/home/runner/work/gate-control/gate-control/backend/core/secrets.py:25`)

These are pragmatic choices, but they blend deployment/runtime policy into application code.

### 7.6 Inconsistent domain placement

The access-log domain is split across `crud/access_log.py` and `crud/logs.py`, and frontend vehicle form logic exists both as a shared component and as inline route markup:

- write path: `/home/runner/work/gate-control/gate-control/backend/crud/access_log.py:8`
- read path: `/home/runner/work/gate-control/gate-control/backend/api/logs.py:16`
- standalone component: `/home/runner/work/gate-control/gate-control/frontend/src/lib/components/VehicleForm.svelte`
- inline form implementation: `/home/runner/work/gate-control/gate-control/frontend/src/routes/vehicles/+page.svelte:153`

This indicates some duplication and unclear ownership of reusable behavior.

### 7.7 Root directory contains mixed application and tooling concerns

The root currently contains product runtime files (`docker-compose.yml`, `.env.example`, `package.json`) alongside a simulation/dev tool (`simulator.py`). (`/home/runner/work/gate-control/gate-control/simulator.py:1`)

This is manageable now, but root clutter will grow over time.

## 8. Concrete Improvements

### 8.1 Introduce clearer backend boundaries

Suggested reorganization:

```text
backend/
  api/            # HTTP entrypoints only
  services/       # domain/business workflows
  integrations/   # relay hardware, storage, secret providers
  workers/        # long-running/background processes
  core/           # config, db, security, dependency wiring, logging
  crud/
  models/
  schemas/
```

This would prevent `core/` from becoming a permanent catch-all.

### 8.2 Extract service layer from route modules

Move workflow logic out of route files such as:

- `api/webhook.py`
- parts of `api/relay.py`
- parts of `api/vehicles.py`

into explicit application services, so routes become thin adapters.

### 8.3 Separate workers from the API runtime

Promote `run_relay_worker()` and `run_cleanup_service()` into standalone worker entrypoints or separate containers/services. This would improve:

- scale independence
- failure isolation
- deployment clarity
- observability

### 8.4 Make system status persistent or centralized

Replace module-global runtime state in `system_status.py` with:

- Redis, or
- a DB-backed heartbeat record

so status behaves correctly in multi-process environments.

### 8.5 Normalize CRUD/domain layout

Consolidate access-log logic into one entity-oriented module or adopt a consistent rule such as:

- one file per aggregate/entity, or
- one file per use case category

but not a mix.

### 8.6 Remove frontend duplication

Use `VehicleForm.svelte` from the vehicles route instead of maintaining separate inline form markup, or remove the shared component if the route-specific version is the real source of truth.

### 8.7 Improve frontend contract sharing

Generate TypeScript API types from backend OpenAPI to avoid hand-maintained duplicate route-local interfaces.

### 8.8 Reorganize environment and tooling files

Possible root cleanup:

```text
env/
  .env.example
  .env.ci

scripts/
  simulator.py
```

This keeps the root focused on application entrypoints and repository metadata.

### 8.9 Separate deployment policy from app code where possible

Move environment-policy decisions toward:

- deployment configuration
- explicit worker commands
- CI/CD/release config

and keep app startup focused on app initialization rather than environment branching.

## 9. Overall Assessment

The repository is already in a solid early-stage shape:

- backend and frontend are clearly separated
- models, schemas, API, and tests are sensibly organized
- infrastructure and operations files are present and understandable
- docs are comprehensive

The main scalability concern is not chaos, but **boundary erosion**:

- `backend/core/` is too broad
- some HTTP modules contain too much business logic
- workers are embedded in the API process
- a few reusable concerns are duplicated or inconsistently placed

Addressing those boundary issues now would make the project substantially easier to scale in code size, team size, and deployment complexity.
