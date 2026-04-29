# ANPR Gate Control System

End-to-end ANPR gate control platform with FastAPI backend, PostgreSQL storage, SvelteKit frontend, and Docker Compose orchestration.

## Project Structure

- backend: FastAPI API, database models, business logic, media write path
- frontend: SvelteKit admin dashboard (Node adapter)
- docs: governance, API contract, worklog
- scripts: quality gate utilities
- docker-compose.yml: local multi-service runtime
- simulator.py: webhook traffic simulator

## Environment Variables

Use .env.example as the template.

Required backend variables:

- DATABASE_URL
- SECRET_KEY
- FRONTEND_URL
- RELAY_IP
- RELAY_USERNAME
- RELAY_PASSWORD
- WEBHOOK_SHARED_SECRET
- WEBHOOK_AUTH_MODE
- ADMIN_USERNAME
- ADMIN_PASSWORD

Optional backend variables:

- WEBHOOK_HMAC_SECRET
- WEBHOOK_MAX_SKEW_SECONDS
- ACCESS_TOKEN_EXPIRE_MINUTES
- LOG_LEVEL

Frontend variable:

- VITE_API_BASE_URL (usually http://localhost:8000/api)

## Fast Local Start (Backend + Frontend)

Use this mode for daily development without Docker.

### 1) Prepare env files (once)

```bash
cp .env.example .env
cp frontend/.env frontend/.env.local
```

If port 3000 is already used on your machine, update .env:

```bash
FRONTEND_PORT=3001
FRONTEND_URL=http://localhost:3001
```

### 2) Start backend (terminal #1)

Run from project root:

```bash
cd /Users/end-i/work/pet/GateControl/anpr-system
python3 -m venv .venv
./.venv/bin/python -m pip install -r backend/requirements.txt
cd backend
../.venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Backend endpoints:

- API health: http://localhost:8000/health
- Swagger UI: http://localhost:8000/docs

### 3) Start frontend (terminal #2)

Run from project root:

```bash
cd /Users/end-i/work/pet/GateControl/anpr-system/frontend
pnpm install
pnpm dev --host --port 3000
```

Frontend URL:

- http://localhost:3000

If you changed FRONTEND_PORT in .env to 3001, start frontend on 3001:

```bash
pnpm dev --host --port 3001
```

### 4) Login

- Username: admin
- Password: value of ADMIN_PASSWORD from .env (default is change-me)

## Start with Docker Compose

1. Copy and configure environment files:

```bash
cp .env.example .env
cp frontend/.env frontend/.env.local
```

2. Build and run services:

```bash
docker compose up --build
```

3. Open applications:

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Local Quality Gate

Run full checks from project root:

```bash
./scripts/check-all.sh
```

## Automated Versioning and Releases

- The workflow in .github/workflows/ci.yml runs quality checks for push/PR to main.
- The workflow in .github/workflows/versioning.yml runs only after CI success on main.
- It calculates the next semantic version tag using commit messages since the previous release tag:
	- major for BREAKING CHANGE or ! in Conventional Commit header
	- minor for feat
	- patch for all other commits
- It creates and pushes the next vX.Y.Z tag automatically.
- The workflow in .github/workflows/release.yml publishes the GitHub Release from that tag.

Manual override is available from GitHub Actions via workflow_dispatch input bump=major|minor|patch.

## Backup and Restore Runbook

Use these commands from the project root.

### Create backups

1. PostgreSQL dump:

```bash
docker compose exec -T postgres pg_dump -U postgres -d anpr > backup-anpr.sql
```

2. Media files archive:

```bash
docker run --rm -v anpr-system_media_data:/data -v "$PWD":/backup alpine \
	sh -c "cd /data && tar czf /backup/backup-media.tar.gz ."
```

### Restore backups

1. Restore PostgreSQL dump:

```bash
cat backup-anpr.sql | docker compose exec -T postgres psql -U postgres -d anpr
```

2. Restore media archive:

```bash
docker run --rm -v anpr-system_media_data:/data -v "$PWD":/backup alpine \
	sh -c "rm -rf /data/* && tar xzf /backup/backup-media.tar.gz -C /data"
```

Note: adjust volume name if your compose project name differs.

## Webhook Simulator

Send mock ANPR events every 10 seconds:

```bash
pip install requests
WEBHOOK_TOKEN=change-me python simulator.py
```

Optional overrides:

- WEBHOOK_URL
- SIM_INTERVAL_SECONDS

## API Notes

- API contract reference: docs/api-contract.md
- Authentication: Bearer JWT for admin routes
- Webhook auth modes:
	- token: X-Webhook-Token compared with WEBHOOK_SHARED_SECRET
	- hmac: X-Webhook-Timestamp + X-Webhook-Signature (HMAC-SHA256 over timestamp+raw_body)
	- rollout switch: WEBHOOK_AUTH_MODE=token|hmac
