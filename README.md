# ANPR Gate Control System

ANPR gate control platform with FastAPI backend, Svelte frontend, PostgreSQL, and Docker Compose support.

## Project Structure

- `backend/`: FastAPI API, models, business logic, media storage
- `frontend/`: Svelte admin panel
- `docs/`: governance, architecture, API contract, plan, worklog
- `scripts/`: local run and quality scripts
- `docker-compose.yml`: local multi-service runtime
- `simulator.py`: webhook traffic simulator

## Environment

Use root `.env` as the single source for local development.

```bash
cp .env.example .env
```

Both `./scripts/run-backend.sh` and `./scripts/run-frontend.sh` automatically load variables from root `.env`.

Important keys:

- `DATABASE_URL` (local backend: host `localhost`; Docker backend: host `postgres`)
- `BACKEND_PORT` (default in this repo: `8010`)
- `FRONTEND_PORT` (default: `3000`)
- `FRONTEND_URL` (CORS origin for backend)
- `VITE_API_BASE_URL` (frontend API base, usually `http://localhost:8010/api`)

## Quick Start (Local)

1. One-time backend setup:

```bash
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.txt
```

2. Start from project root with npm scripts:

```bash
npm run backend   # backend only
npm run frontend  # frontend only
npm run dev       # backend + frontend
npm run doctor    # health + CORS diagnostics
npm run smoke     # login/status/stats/logs smoke flow
npm run smoke:critical # allowed/blocked webhook decision flow
```

Equivalent direct scripts:

```bash
./scripts/run-backend.sh
./scripts/run-frontend.sh
./scripts/run-dev.sh
./scripts/doctor.sh
./scripts/smoke-e2e.sh
```

Local endpoints (with defaults):

- Frontend: `http://localhost:3000`
- Backend health: `http://localhost:8010/health`
- Swagger UI: `http://localhost:8010/docs`

Default login:

- Username: `admin`
- Password: value of `ADMIN_PASSWORD` in `.env`

## Docker Compose

1. Prepare env:

```bash
cp .env.example .env
```

2. Run stack:

```bash
docker compose up --build
```

Compose ports are controlled by `.env`:

- `POSTGRES_PORT` -> Postgres host port
- `BACKEND_PORT` -> backend host port (container still listens on 8000)
- `FRONTEND_PORT` -> frontend host port

## Quality and Coverage

Run full quality gate:

```bash
./scripts/check-all.sh
```

Run full gate with coverage:

```bash
RUN_COVERAGE=1 ./scripts/check-all.sh
```

Run coverage only:

```bash
./scripts/coverage-all.sh
```

## Backup and Restore (PostgreSQL)

These scripts work with the running Docker Compose `postgres` service.

Create backup:

```bash
./scripts/backup-postgres.sh
```

or

```bash
npm run backup:db
```

Restore from backup:

```bash
./scripts/restore-postgres.sh ./backups/postgres-anpr-YYYYMMDDTHHMMSSZ.dump
```

or

```bash
npm run restore:db -- ./backups/postgres-anpr-YYYYMMDDTHHMMSSZ.dump
```

Backend coverage gate is enforced by `BACKEND_COVERAGE_MIN` (default `70`).

Frontend coverage thresholds (Vitest):

- statements >= 95
- lines >= 95
- functions >= 90
- branches >= 65

## Troubleshooting

- `Address already in use`: check listeners with `lsof -nP -iTCP:<port> -sTCP:LISTEN`.
- `ERR_CONNECTION_REFUSED`: make sure frontend `VITE_API_BASE_URL` and backend `BACKEND_PORT` match.
- CORS errors: run `npm run doctor` and confirm `FRONTEND_URL` matches the browser origin.
- Local backend DB connection: for local run use `DATABASE_URL` host `localhost`; for compose backend use host `postgres`.

## Security Notes

- Set strong values for `SECRET_KEY`, `ADMIN_PASSWORD`, `WEBHOOK_SHARED_SECRET`.
- In non-development environments (`APP_ENV` not `development/local/test/dev`), backend refuses to start with `change-me` secrets.

## Media Upload Limits

- Allowed webhook image content types: `image/jpeg`, `image/png`, `image/webp`.
- Max image payload is controlled by `WEBHOOK_MAX_IMAGE_BYTES` (default `5242880`, 5 MB).

## Relay Queue Processing

- Webhook/manual trigger paths enqueue relay jobs into `relay_jobs`.
- Background worker processes queue asynchronously with retry and dead-letter states.
- Worker behavior is configurable with:
	- `RELAY_WORKER_POLL_SECONDS`
	- `RELAY_WORKER_RETRY_SECONDS`
	- `RELAY_WORKER_MAX_ATTEMPTS`

## Documentation

- Governance: `docs/GOVERNANCE.md`
- API contract: `docs/api-contract.md`
- Architecture: `docs/architecture.md`
- Data flow (Mermaid): `docs/data-flow.mmd`
- Project structure reference: `docs/project-structure-reference.md`
- Plan: `docs/plan.md`
- Worklog: `docs/worklog.md`
- Production runbook: `docs/runbook-production.md`
- SLO/alerting baseline: `docs/slo-alerting-baseline.md`

## Database Migrations (Alembic)

Migration policy:

- Production/staging: Alembic is the source of truth for schema changes.
- Local dev/test: `create_all` runs only in local/dev/test environments by default (or via `AUTO_CREATE_SCHEMA=1`).

Run from project root:

```bash
backend/.venv/bin/python -m alembic -c backend/alembic.ini upgrade head
```

Create a new migration after model changes:

```bash
backend/.venv/bin/python -m alembic -c backend/alembic.ini revision --autogenerate -m "describe change"
backend/.venv/bin/python -m alembic -c backend/alembic.ini upgrade head
```

## Webhook Simulator

```bash
pip install requests
WEBHOOK_TOKEN=change-me python simulator.py
```
