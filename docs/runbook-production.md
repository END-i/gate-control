# Production Runbook (Baseline)

## Scope

This runbook describes first-response steps for critical ANPR platform incidents in production-like environments.

## Service Inventory

- API: FastAPI backend (`/health`, `/api/*`, `/metrics`)
- UI: Svelte frontend
- DB: PostgreSQL
- Security scan lane: ZAP baseline report artifact in CI

## SLO Targets (Initial)

- API availability: 99.9%
- Webhook decision latency (p95): <= 500 ms
- Webhook processing success ratio: >= 99.5%
- Manual trigger endpoint success ratio: >= 99%

## Alert Thresholds (Initial)

- `5xx` error ratio > 2% for 5 minutes
- `/health` unavailable for 2 consecutive probes
- No webhook events for expected active period >= 10 minutes
- Relay failures > 10% in 5 minutes
- DB readiness check failures > 3 consecutive checks

## Incident Response

### 1. API unavailable

1. Check backend health endpoint.
2. Check backend container status and recent logs.
3. Validate DB connectivity and migration state.
4. If unresolved in 15 minutes, rollback to N-1 image.

### 2. Webhook ingestion degraded

1. Verify webhook auth mode and secrets (`WEBHOOK_AUTH_MODE`, `WEBHOOK_SHARED_SECRET`, `WEBHOOK_HMAC_SECRET`).
2. Check camera ITSAPI notification target URL is pointing to the correct backend endpoint.
3. Send a synthetic webhook test event via `simulator.py` or `scripts/smoke-critical-flow.sh`.
4. Check logs for signature/token failures and payload validation errors.
5. If camera is sending events but backend rejects: verify field names (`plateNumber`/`plate_number`) and auth headers.
6. If systemic, switch traffic to fallback/manual access protocol.

### 3. Relay trigger failures

1. Inspect relay endpoint reachability (`RELAY_IP`).
2. Verify relay credentials (`RELAY_USERNAME`, `RELAY_PASSWORD`) and timeout behavior.
3. Confirm decision path still records access logs even when relay fails.
4. If using camera DO relay: verify physical wiring of relay output to barrier controller.
5. Escalate to hardware/network operator if external dependency is down.

### 4. Camera hardware outage (Dahua ITC413-PW4D-IZ1)

1. Confirm no ITSAPI events received for >10 min (alert: `No webhook events for >= 10 minutes`).
2. Check camera power (PoE 802.3at or 12 V DC) and network link (RJ-45).
3. Access camera web UI to verify ITSAPI notification target is configured correctly.
4. Camera on-board MicroSD may store snapshots locally during outage — review for audit if needed.
5. Escalate to hardware operator for physical inspection if reachable but non-functional.

### 4. Database incident

1. Verify postgres readiness.
2. Run backup immediately before invasive actions.
3. Restore from latest valid backup if integrity is compromised.
4. Validate API read/write flows after restore.

## Backup and Restore Operations

- Create backup: `./scripts/backup-postgres.sh`
- Restore backup: `./scripts/restore-postgres.sh <path-to-backup.dump>`
- Nightly drill workflow: `.github/workflows/backup-restore-drill.yml`

## Post-Incident Checklist

1. Record timeline and root cause.
2. Add regression test or monitor for the incident class.
3. Update runbook and alert thresholds if needed.
4. Track follow-up tasks in `docs/plan.md`.
