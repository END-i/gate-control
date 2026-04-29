# Governance for Full Autopilot Delivery

## Purpose
This document defines mandatory execution rules for autonomous development of the ANPR Gate Control project.

## Scope
These rules apply to all prompts in the blueprint from Prompt 0 through Prompt 34.

## Global Definition of Done
A prompt is complete only when all items are true:

1. The requested feature is implemented exactly as specified.
2. Required files are created or updated.
3. API behavior matches the contract in docs/api-contract.md.
4. Relevant tests for changed behavior pass.
5. No lint/typecheck errors remain in touched areas.
6. The prompt has one dedicated commit following commit policy.
7. The prompt worklog includes executed commands and validation results.

## Per-Prompt DoD Checklist Template
Use this checklist for each prompt:

- Prompt ID:
- Goal summary:
- Files changed:
- Commands executed:
- Tests/checks executed:
- Result of checks:
- Known limitations (if any):
- Commit hash:
- Status: done | blocked

## Default Decisions
Use these defaults without asking clarifying questions unless explicitly overridden by prompt text:

1. Timezone: UTC.
2. Datetime format in API payloads: ISO-8601 UTC with Z suffix.
3. Pagination defaults: limit=50, offset=0.
4. Pagination max limit: 200.
5. API error response format: {"detail":"..."}.
6. Vehicle status default: blocked.
7. UI language default: en.
8. CSV export encoding: UTF-8.
9. File path separator in stored media paths: /.
10. Test mode database: SQLite (temporary, isolated).

## API Contract Policy
All endpoints must conform to docs/api-contract.md:

1. Explicit request and response schemas.
2. Explicit status codes for success and failure.
3. Error payloads must use the default error format.
4. Date filtering semantics must be explicit and UTC-based.
5. Pagination envelope must be consistent across list endpoints.

## Validation Pipeline
The agent must run checks before closing each prompt.

### Backend
1. Lint: ruff check backend
2. Typecheck: mypy backend
3. Tests: pytest backend/tests -q

### Frontend
1. Lint: pnpm --dir frontend lint
2. Typecheck: pnpm --dir frontend check
3. Tests: pnpm --dir frontend test -- --run

### Container
1. Build backend image: docker build -t anpr-backend ./backend
2. Build frontend image: docker build -t anpr-frontend ./frontend

If a check fails, the agent must fix issues and re-run failed checks until green or until stop conditions are met.

## Commit Policy
1. One prompt equals one commit.
2. Commit message format: prompt-<number>: <short action>.
3. Commit body must include:
- files changed
- commands executed
- validation summary
4. No amend unless explicitly requested.
5. No unrelated refactors in prompt commits.

## Autopilot Stop Conditions
The agent may stop only when one of these conditions is true:

1. Required secrets or credentials are unavailable.
2. A destructive migration needs explicit human approval.
3. External dependency is unreachable and blocks progress.
4. The same failing issue persists after 3 fix attempts.
5. Requested task conflicts with explicit higher-priority policy.

In all other cases, the agent must continue automatically.

## Environment Contract
All required variables must be declared in .env.example and validated at startup.

Critical variables must fail fast if missing:

1. DATABASE_URL
2. SECRET_KEY
3. FRONTEND_URL
4. RELAY_IP
5. RELAY_USERNAME
6. RELAY_PASSWORD
7. WEBHOOK_SHARED_SECRET
8. WEBHOOK_AUTH_MODE

Optional variables must have safe defaults:

1. WEBHOOK_MAX_SKEW_SECONDS=300
2. LOG_LEVEL=INFO
3. ACCESS_TOKEN_EXPIRE_MINUTES=60

## Quality Gate for Project Completion
Project is complete only if full gate passes:

1. Backend lint/type/tests pass.
2. Frontend lint/type/tests pass.
3. Docker images build successfully.
4. Integration flow is manually verified:
- webhook ingestion
- access decision
- log persistence
- media serving
- dashboard rendering

## Required Automation Script
A root script scripts/check-all.sh must execute full validation in order:

1. backend lint
2. backend typecheck
3. backend tests
4. frontend lint
5. frontend typecheck
6. frontend tests
7. backend docker build
8. frontend docker build

Exit with non-zero code on first failure.

## Worklog Format
For each prompt, append a worklog entry in docs/worklog.md:

1. Prompt number and title.
2. Summary of implementation.
3. Files changed.
4. Commands run.
5. Validation results.
6. Commit hash.
7. Next prompt readiness: yes | no.

## Security Baseline
1. Never log secrets or full signatures.
2. Use constant-time compare for secret checks.
3. Validate and sanitize all input.
4. Use explicit timeouts on outbound HTTP calls.
5. Keep webhook auth behind configurable mode for controlled rollout.

## Change Control
1. Avoid modifying previous prompt outputs unless required by current prompt.
2. If modification is required, document why in worklog.
3. Keep architecture and naming consistent with blueprint.

## Enforcement
Any output that violates this document is considered incomplete and must be corrected before proceeding.
