# SLO and Alerting Baseline

## Objectives

Define measurable reliability targets and actionable alerts for ANPR production readiness.

## SLIs

- API availability: successful `/health` checks / total checks
- Decision latency: webhook request duration (p50/p95/p99)
- Decision correctness proxy: expected allowed/blocked response ratio anomalies
- Relay outcome ratio: relay success / relay attempts
- Auth stability: login success ratio and 401 spike rate

## SLOs

- Availability >= 99.9% monthly
- Webhook p95 latency <= 500 ms
- Relay success ratio >= 99% over rolling 1h
- Login success ratio >= 98% (excluding bad credential attacks)

## Alert Rules

- Critical: backend unavailable for 2 consecutive probes
- High: webhook p95 latency > 1s for 10 minutes
- High: relay success ratio < 95% for 10 minutes
- Medium: auth 401 spike > 3x baseline for 15 minutes
- Medium: DAST report generation failure in CI

## Dashboards

- API health and error ratio
- Webhook throughput and latency
- Relay trigger outcomes
- Auth success/failure trends
- Database readiness and connection errors

## Review Cadence

- Weekly: threshold tuning and false-positive review
- Monthly: SLO attainment report and remediation planning
