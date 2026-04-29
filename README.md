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
