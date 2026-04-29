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
```

Equivalent direct scripts:

```bash
./scripts/run-backend.sh
./scripts/run-frontend.sh
./scripts/run-dev.sh
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

Frontend coverage thresholds (Vitest):

- statements >= 95
- lines >= 95
- functions >= 90
- branches >= 65

## Documentation

- Governance: `docs/GOVERNANCE.md`
- API contract: `docs/api-contract.md`
- Architecture: `docs/architecture.md`
- Plan: `docs/plan.md`
- Worklog: `docs/worklog.md`

## Webhook Simulator

```bash
pip install requests
WEBHOOK_TOKEN=change-me python simulator.py
```
