# Project Structure Reference (Detailed)

This document describes the practical purpose of each important file and directory in the repository.
It is intended as an onboarding and maintenance reference.

## Root

- `.env`: Local runtime configuration (not committed). Single source for local backend/frontend scripts.
- `.env.example`: Template of required and optional environment variables and safe defaults.
- `.gitignore`: Ignore policy for generated artifacts, secrets, caches, uploads, and logs.
- `README.md`: Main operational documentation (run, troubleshoot, quality, security notes).
- `package.json`: Root scripts entrypoint for backend/frontend/dev/doctor/smoke/precommit.
- `docker-compose.yml`: Multi-service local orchestration (postgres + backend + frontend).
- `simulator.py`: Camera webhook event emulator for local/manual load simulation.

## CI / Automation

- `.github/workflows/ci.yml`: CI quality checks for pushes/PRs.
- `.github/workflows/versioning.yml`: Automated semantic tag generation.
- `.github/workflows/release.yml`: GitHub release publication flow.

## Backend (`backend/`)

### Core app runtime

- `backend/main.py`: FastAPI app composition, middleware, CORS, static mount, lifecycle startup/shutdown.
- `backend/requirements.txt`: Backend dependencies (runtime, tests, lint/type tools).
- `backend/Dockerfile`: Container image build for backend service.

### Database access and configuration

- `backend/core/config.py`: Typed settings via pydantic-settings (`.env` loading and aliases).
- `backend/core/database.py`: SQLAlchemy engine/session factory and schema initialization policy.
- `backend/models/base.py`: SQLAlchemy declarative base class.
- `backend/models/admin.py`: Admin auth model.
- `backend/models/vehicle.py`: Vehicle whitelist/blacklist model and status enum.
- `backend/models/access_log.py`: Access event model with image path reference.
- `backend/models/__init__.py`: Model export module.

### Migrations (Alembic)

- `backend/alembic.ini`: Alembic config (script location and logging).
- `backend/alembic/env.py`: Alembic migration environment with async URL handling.
- `backend/alembic/script.py.mako`: Revision template.
- `backend/alembic/README`: Local usage notes for Alembic.
- `backend/alembic/versions/0001_initial_schema.py`: Initial schema migration.
- `backend/alembic_commands.md`: Migration command reference.

### API routers

- `backend/api/router.py`: Top-level `/api` router composition.
- `backend/api/auth.py`: Login and `/auth/me` endpoints.
- `backend/api/vehicles.py`: Vehicle CRUD API with validation and pagination.
- `backend/api/logs.py`: Logs listing, filtering, and SSE stream endpoint.
- `backend/api/stats.py`: Aggregated dashboard statistics endpoint.
- `backend/api/system.py`: System heartbeat/status endpoint.
- `backend/api/relay.py`: Manual relay trigger endpoint.
- `backend/api/webhook.py`: Camera webhook intake, auth verification, media persistence, access decision.
- `backend/api/__init__.py`: Router package marker.

### Business and infrastructure services

- `backend/core/security.py`: Password hashing and JWT token utilities.
- `backend/core/dependencies.py`: Auth dependencies and current admin resolution.
- `backend/core/hardware.py`: Camera relay call implementation and timeout handling.
- `backend/core/rate_limit.py`: In-memory request limiting helpers.
- `backend/core/system_status.py`: Last webhook timestamp tracking for online/offline status.
- `backend/core/seed.py`: Initial admin bootstrap logic.
- `backend/core/cleanup.py`: Retention cleanup for stale logs and image files.
- `backend/core/logging_config.py`: Loguru setup for console/file logs and rotation.
- `backend/core/__init__.py`: Core package marker.

### CRUD layer

- `backend/crud/admin.py`: Admin queries.
- `backend/crud/vehicle.py`: Vehicle data operations.
- `backend/crud/access_log.py`: Access log write operations.
- `backend/crud/logs.py`: Access logs list/filter and stream support queries.
- `backend/crud/stats.py`: Aggregate counts for dashboard stats.
- `backend/crud/__init__.py`: CRUD package marker.

### Schemas

- `backend/schemas/auth.py`: Auth request/response schemas.
- `backend/schemas/vehicle.py`: Vehicle API schemas.
- `backend/schemas/log.py`: Access log API schemas.
- `backend/schemas/stats.py`: Dashboard stats schema.
- `backend/schemas/__init__.py`: Schemas package marker.

### Backend tests

- `backend/tests/conftest.py`: Shared fixtures (test DB, app dependency overrides, seeded admin).
- `backend/tests/test_auth_login.py`: Auth login and `/auth/me` behavior tests.
- `backend/tests/test_vehicles.py`: Vehicle endpoint auth + CRUD path tests.
- `backend/tests/test_webhook_auth.py`: Token/HMAC webhook auth tests.
- `backend/tests/test_security_and_validation.py`: Security checks, CORS, webhook media validation tests.
- `backend/tests/__init__.py`: Tests package marker.

### Runtime artifact directories (generated)

- `backend/media/`: Uploaded ANPR images (runtime generated, gitignored).
- `backend/logs/`: Rolling log files (runtime generated, gitignored).

## Frontend (`frontend/`)

### Frontend app/runtime configs

- `frontend/package.json`: Frontend scripts and dependencies.
- `frontend/pnpm-lock.yaml`: Dependency lockfile.
- `frontend/pnpm-workspace.yaml`: pnpm workspace config.
- `frontend/svelte.config.js`: SvelteKit configuration.
- `frontend/vite.config.ts`: Vite bundler config.
- `frontend/vitest.config.ts`: Test runner config and coverage thresholds.
- `frontend/tsconfig.json`: TypeScript config.
- `frontend/Dockerfile`: Multi-stage frontend image build.
- `frontend/README.md`: Generated frontend scaffold notes.
- `frontend/.gitignore`: Frontend-specific ignored files.
- `frontend/.npmrc`: npm/pnpm behavior options.

### App source

- `frontend/src/app.html`: HTML shell template for Svelte app.
- `frontend/src/app.d.ts`: App-level TypeScript declarations.

### Shared frontend lib

- `frontend/src/lib/api.ts`: Typed API wrapper (auth header, 401 handling).
- `frontend/src/lib/i18n.ts`: i18n initialization and locale management.
- `frontend/src/lib/index.ts`: Barrel exports.
- `frontend/src/lib/stores/auth.ts`: Auth token state management.
- `frontend/src/lib/assets/favicon.svg`: App icon asset.
- `frontend/src/lib/components/ImageModal.svelte`: Modal for displaying captured images.
- `frontend/src/lib/components/LanguageSwitcher.svelte`: Locale switch UI.
- `frontend/src/lib/components/SystemStatusIndicator.svelte`: Header status indicator UI.
- `frontend/src/lib/components/VehicleForm.svelte`: Vehicle create/edit form component.

### Pages/routes

- `frontend/src/routes/+layout.svelte`: Main authenticated shell/layout.
- `frontend/src/routes/+page.svelte`: Dashboard home page.
- `frontend/src/routes/layout.css`: Global route-level styles.
- `frontend/src/routes/login/+page.svelte`: Login page.
- `frontend/src/routes/vehicles/+page.svelte`: Vehicle management page.
- `frontend/src/routes/logs/+page.svelte`: Access logs page (filters, pagination, CSV, image modal, SSE).

### Localization

- `frontend/src/locales/en.json`: English dictionary.
- `frontend/src/locales/ru.json`: Russian dictionary.
- `frontend/src/locales/uk.json`: Ukrainian dictionary.
- `frontend/src/locales/bg.json`: Bulgarian dictionary.

### Frontend tests

- `frontend/src/tests/setup.ts`: Testing runtime setup.
- `frontend/src/tests/LanguageSwitcher.test.ts`: Locale switch behavior tests.
- `frontend/src/tests/VehicleForm.test.ts`: Vehicle form validation tests.

### Static assets

- `frontend/static/robots.txt`: Robots policy for app.

### Editor hints

- `frontend/.vscode/extensions.json`: Recommended VS Code extensions.
- `frontend/.vscode/settings.json`: Frontend-local editor settings.

## Scripts (`scripts/`)

- `scripts/run-backend.sh`: Backend runner with root `.env` loading.
- `scripts/run-frontend.sh`: Frontend runner with root `.env` loading.
- `scripts/run-dev.sh`: Combined local runner (backend + frontend) with process cleanup trap.
- `scripts/check-all.sh`: Local quality gate (lint, typecheck, tests, docker builds, optional coverage).
- `scripts/coverage-all.sh`: Unified backend/frontend coverage run with backend fail-under threshold.
- `scripts/doctor.sh`: Runtime diagnostics (health, CORS, frontend reachability).
- `scripts/smoke-e2e.sh`: API smoke flow (login/me/status/stats/logs).
- `scripts/lib/load-env.sh`: Shared `.env` parser/loader used by run scripts.

## Documentation (`docs/`)

- `docs/GOVERNANCE.md`: Operational development governance and quality rules.
- `docs/api-contract.md`: API contract reference.
- `docs/architecture.md`: System architecture details.
- `docs/data-flow.mmd`: Mermaid data-flow diagram.
- `docs/plan.md`: Master implementation blueprint + execution status + operational plans.
- `docs/worklog.md`: Chronological implementation notes.
- `docs/releases/v0.1.0.md`: Release notes.
- `docs/releases/v0.1.3.md`: Release notes.

## Notes on Generated/Excluded Files

The repository intentionally excludes runtime and generated artifacts (venvs, node_modules, caches, coverage reports, uploaded media, logs, local DB files). Those files are environment-specific and not source-of-truth.
