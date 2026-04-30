# AI Development Blueprint: ANPR Gate Control System

## AI Agent Rules of Engagement (System Prompt)

Before executing any prompt from this blueprint, the AI agent must strictly adhere to the following behavioral rules:

1.  **Strict Scope Adherence:** Execute ONLY the specific task requested in the current prompt. Do not invent, assume, or implement unrequested features, UI components, or business logic.
2.  **Sequential Execution:** Follow the development plan strictly step-by-step. Do not write code for future steps or anticipate upcoming requirements.
3.  **Zero Assumptions (Ask First):** If a prompt is ambiguous, lacks specific technical details, or requires a design decision not covered in the instructions, halt execution. Ask a clear, specific clarifying question and wait for the user's answer before writing code.
4.  **Minimal Output:** Provide the requested code with zero conversational filler. Eliminate greetings, conclusions, and unnecessary explanations. Output only the code, terminal commands, and brief structural comments.
5.  **No Unprompted Refactoring:** Do not modify, rewrite, or restructure previously generated code or files unless explicitly instructed by the current prompt.
6.  **Code Completeness:** When generating a file, provide the complete, functional code for that specific step. Do not use placeholders like `// ...existing code...` or `// implement later` unless explicitly instructed.
7.  **Contextual Example Awareness:** Before generating code, analyze any provided code examples in this blueprint. Treat these examples as style references for architecture and naming, not as copy-paste complete implementations. Ensure all generated code is runnable and all imports/dependencies are explicit.
8. **Technology Stack Consistency:**
Always strictly use the following stack for any code generation:
* **Backend:** Python 3.11, FastAPI, SQLAlchemy 2.0 (Async), PostgreSQL.
* **Frontend:** SvelteKit (Node.js Adapter), Tailwind CSS, svelte-i18n.
* **Infrastructure:** Docker, Docker Compose.
9. **API Contract Consistency:** If a frontend step depends on a backend endpoint, that endpoint must be explicitly introduced in an earlier backend prompt before frontend implementation.
10. **Security by Default:** Any external callback endpoint (camera webhook, relay trigger) must include an authentication/verification mechanism and explicit failure handling.

---

## Project Structure

```text
anpr-system/
├── backend/                # FastAPI Application
│   ├── alembic/            # Database migrations
│   ├── api/                # API Routes (v1)
│   │   ├── auth.py
│   │   ├── vehicles.py
│   │   └── logs.py
│   ├── core/               # Config, Security, Constants
│   ├── crud/               # DB Operations logic
│   ├── models/             # SQLAlchemy Models
│   ├── schemas/            # Pydantic Schemas
│   ├── media/              # Local storage for images (gitignored)
│   ├── tests/              # Pytest automated tests
│   ├── main.py             # Entry point
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/               # SvelteKit Application
│   ├── src/
│   │   ├── lib/            # Reusable components & API client
│   │   │   ├── api.ts
│   │   │   ├── stores/
│   │   │   ├── i18n.ts     # Localization config
│   │   │   └── components/
│   │   ├── locales/        # Translation dictionaries (en, ru, uk, bg)
│   │   ├── routes/         # Pages (Login, Dashboard, Logs)
│   │   ├── tests/          # Vitest automated tests
│   │   └── app.html
│   ├── static/             # Assets
│   ├── svelte.config.js
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml      # Orchestration
└── .env                    # Global environment variables
```

---

## Reference Code Examples

### 1. Backend: FastAPI Webhook

```python
# backend/api/logs.py
from fastapi import APIRouter, UploadFile, File, Form, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from crud import vehicle as vehicle_crud
from core.hardware import trigger_relay

router = APIRouter()

@router.post("/webhook/anpr")
async def handle_camera_event(
    plate_number: str = Form(...),
    image: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    # 1. Normalize plate
    clean_plate = plate_number.replace(" ", "").upper()
    
    # 2. Check access
    is_allowed = await vehicle_crud.check_access(db, clean_plate)
    
    # 3. Save image and log event
    image_path = await save_image_async(image)
    await logs_crud.create_log(db, clean_plate, is_allowed, image_path)
    
    # 4. Hardware Action
    if is_allowed:
        await trigger_relay()
        return {"status": "opened", "plate": clean_plate}
        
    return {"status": "denied", "plate": clean_plate}
```

### 2. Frontend: SvelteKit Reactive Table

```svelte
<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '$lib/api';
  import LogRow from '$lib/components/LogRow.svelte';

  let logs = [];
  let loading = true;

  onMount(async () => {
    logs = await api.get('/logs?limit=50');
    loading = false;
    
    // Setup SSE for real-time updates
    const eventSource = new EventSource(`${import.meta.env.VITE_API_BASE_URL}/logs/stream`);
    eventSource.onmessage = (event) => {
      const newLog = JSON.parse(event.data);
      logs = [newLog, ...logs]; // Reactive update
    };
  });
</script>

<div class="p-6">
  <h1 class="text-2xl font-bold mb-4">Access Logs</h1>
  {#if loading}
    <p>Loading...</p>
  {:else}
    <table class="min-w-full bg-white border">
      <thead>
        <tr class="bg-gray-100">
          <th>Time</th>
          <th>Plate</th>
          <th>Status</th>
          <th>Photo</th>
        </tr>
      </thead>
      <tbody>
        {#each logs as log}
          <LogRow {log} />
        {/each}
      </tbody>
    </table>
  {/if}
</div>
```

---

## Step-by-Step Prompt Execution Plan

### Phase 0: Project Initialization
1.  **Prompt 0 (Root Setup):** "Generate terminal commands to create a root directory named `anpr-system`. Inside this directory, initialize a Git repository. Create two subdirectories named `backend` and `frontend`. Create a root `.gitignore` file configured to ignore standard Python, Node.js, and OS-generated files. Create an initial `README.md` file with the project title."

### Phase 0.5: Autopilot Governance (Mandatory)
This phase defines non-negotiable execution rules for fully autonomous agent development.

1. **Prompt 0.5.1 (Global Definition of Done):** "Create a `GOVERNANCE.md` file at project root. Define per-prompt completion criteria: required files changed, required commands executed, and required tests/checks passed. Mark a prompt as complete only when all criteria are satisfied."
2. **Prompt 0.5.2 (Default Decision Matrix):** "Add a section to `GOVERNANCE.md` named `Default Decisions` with fixed defaults to avoid blocking questions: timezone=UTC, datetime format=ISO-8601 with `Z`, pagination defaults `limit=50 offset=0`, API error format `{\"detail\":\"...\"}`, vehicle status default=`blocked`, and language default=`en`."
3. **Prompt 0.5.3 (API Contract Template):** "Create `docs/api-contract.md` with canonical request/response schemas, status codes, pagination envelope, and filtering semantics. All newly added endpoints must conform to this document unless explicitly overridden in a prompt."
4. **Prompt 0.5.4 (Validation Pipeline):** "Define and document mandatory verification commands in `GOVERNANCE.md`: backend lint/type/test, frontend lint/type/test, and Docker build checks. If any check fails, the agent must fix issues before moving to the next prompt."
5. **Prompt 0.5.5 (Commit Strategy):** "Define commit policy in `GOVERNANCE.md`: one prompt = one commit, commit message format `prompt-<number>: <short action>`, include changed files list and validation summary in commit body."
6. **Prompt 0.5.6 (Autopilot Stop Conditions):** "Define strict stop conditions in `GOVERNANCE.md`: stop only for missing secrets, destructive migrations requiring approval, external service credentials unavailable, or irreproducible failing tests after 3 fix attempts. Otherwise continue automatically."
7. **Prompt 0.5.7 (Environment Contract):** "Create `.env.example` with all required variables across backend/frontend/docker/testing, include comments for format and safe defaults, and require startup validation that fails fast on missing critical variables."
8. **Prompt 0.5.8 (Final Quality Gate):** "Add `scripts/check-all.sh` to run the full project gate (lint, typecheck, unit tests, build). Update `README.md` to define project completion as successful execution of this script."

### Phase 1: Backend Setup & Database (FastAPI + PostgreSQL)
2.  **Prompt 1 (Project Structure & CORS):** "Set up a FastAPI project structure. Configure an asynchronous PostgreSQL connection using SQLAlchemy 2.0 and `asyncpg`. Implement Pydantic `BaseSettings` to load environment variables (DATABASE_URL, SECRET_KEY, RELAY_IP, RELAY_USERNAME, RELAY_PASSWORD, FRONTEND_URL, WEBHOOK_SHARED_SECRET). Configure FastAPI CORS middleware to allow requests from `FRONTEND_URL`."
3.  **Prompt 2 (Data Models):** "Write SQLAlchemy models: `Admin` (id, username, hashed_password), `Vehicle` (id, license_plate [unique, indexed], status enum: allowed|blocked, owner_info), and `AccessLog` (id, license_plate, timestamp [indexed], access_granted, image_path). Generate Alembic initialization plus first migration and upgrade commands."

### Phase 2: Backend Security & Auth
4.  **Prompt 3 (JWT & Hashing):** "Create a security module. Implement password hashing using `passlib` (bcrypt) and functions to generate and verify JWT tokens using `PyJWT`."
5.  **Prompt 4 (Auth Endpoints & Seeding):** "Implement a `/api/auth/login` endpoint to validate admin credentials and return an access token. Create a `get_current_admin` dependency using `OAuth2PasswordBearer` to protect routes. Add a database startup event or a standalone CLI script to seed the initial admin user from environment variables (`ADMIN_USERNAME`, `ADMIN_PASSWORD`) if the database is empty; fail with a clear error if variables are missing."

### Phase 3: Backend Business Logic & API
6.  **Prompt 5 (Vehicle CRUD):** "Create Pydantic schemas and async CRUD functions for the `Vehicle` model. Implement a router `/api/vehicles` protected by `get_current_admin`, including server-side pagination for the GET method."
7.  **Prompt 6 (Camera Webhook):** "Create an endpoint `/api/webhook/anpr` to accept `multipart/form-data` (text field `plate_number` and binary file `image`). Verify request authenticity using header `X-Webhook-Token` matched against `WEBHOOK_SHARED_SECRET` (constant-time comparison). Use `aiofiles` to save the image asynchronously to a local `media/YYYY/MM/DD/` directory and return the relative path."
8.  **Prompt 7 (Access Logic):** "Update the `/api/webhook/anpr` endpoint. Add logic to query the `Vehicle` database for the received `plate_number`. If found and status is 'allowed', record `access_granted=True` in `AccessLog` and trigger the relay. Otherwise, record as `False`."
9.  **Prompt 8 (Hardware Relay Integration):** "Write an async function `trigger_relay()` using `httpx`. It must send an HTTP POST request to the camera's relay IP address using Basic Auth (credentials loaded from environment variables) with a 2-second timeout, return a success/failure result, and log non-2xx responses/timeouts without crashing webhook processing."
10. **Prompt 9 (Logs API):** "Implement a `/api/logs` router. Add a GET endpoint with pagination (`limit`, `offset`) and filtering by date and plate; define date filters in UTC with explicit inclusive `date_from`/`date_to` semantics. Mount `StaticFiles` in the main application to serve images from the `/media` directory."
11. **Prompt 10 (Statistics API):** "Create a `/api/stats` endpoint. Execute async SQL count queries to return total vehicles in the database, today's total access logs, and today's denied access attempts."
12. **Prompt 11 (Real-time SSE):** "Implement an endpoint `/api/logs/stream` using an async generator or `sse-starlette` to push Server-Sent Events (SSE) to authenticated clients whenever a new `AccessLog` entry is created. Include heartbeat events and proper disconnect handling. For browser compatibility, authenticate SSE via secure HttpOnly cookie session or a short-lived signed query token (native `EventSource` cannot send custom Authorization headers)."
13. **Prompt 11.1 (Manual Relay Endpoint):** "Implement an authenticated endpoint `/api/relay/trigger` for manual gate opening from the dashboard header button. Reuse `trigger_relay()` and return clear success/error payloads."

### Phase 4: Frontend Setup & Auth (SvelteKit)
14. **Prompt 12 (Initialization):** "Generate commands to initialize a SvelteKit project. Add Tailwind CSS, PostCSS, and `@sveltejs/adapter-node`. Create a `.env` file with `VITE_API_BASE_URL`."
15. **Prompt 13 (API Client):** "Write a global API client wrapper using `fetch`. It must automatically append the `Authorization: Bearer <token>` header, use the base URL from environment variables, and handle 401 Unauthorized errors by clearing state."
16. **Prompt 14 (Login View):** "Create the `/login/+page.svelte` component. Build a login form, implement the POST request to the auth endpoint, save the returned JWT in a Svelte store, and redirect to the dashboard."
17. **Prompt 15 (Layout & Navigation):** "Develop `+layout.svelte`. Include a sidebar with navigation links (Dashboard, Vehicles, Logs) and a header containing a 'Manual Trigger' button that sends an authenticated request to `/api/relay/trigger`."

### Phase 5: Frontend UI & Features
18. **Prompt 16 (Dashboard):** "Create the main `+page.svelte` (Dashboard). Fetch data from the statistics API and display it using styled Tailwind CSS widget cards."
19. **Prompt 17 (Vehicle Management):** "Build the `/vehicles/+page.svelte` component. Display a table of vehicles. Implement a modal form to add or edit license plates with regex validation, and add delete confirmation functionality."
20. **Prompt 18 (Access Logs Grid):** "Create the `/logs/+page.svelte` component. Build a data grid that fetches access logs with server-side pagination parameters. Include input filters for date ranges and license plate searches."
21. **Prompt 19 (Media & Export):** "Add a 'Download CSV' button to the logs page to export the current view using backend query parameters consistent with the active filters. Create an `ImageModal.svelte` component that opens upon clicking a log row to display the linked photograph."
22. **Prompt 20 (SSE Integration):** "Update the logs page to connect to the backend's SSE stream via `EventSource`. Prepend new access events to the top of the log table dynamically without requiring a page refresh."

### Phase 6: Localization (i18n)
23. **Prompt 21 (i18n Setup):** "Install the `svelte-i18n` library. Create a `src/locales` directory and basic JSON dictionary files for four languages: `en.json` (English), `ru.json` (Russian), `uk.json` (Ukrainian), and `bg.json` (Bulgarian). Write the `src/lib/i18n.ts` file to configure and initialize the dictionaries."
24. **Prompt 22 (Language Switcher):** "Create a `LanguageSwitcher.svelte` component. Implement a dropdown UI for language selection (EN, RU, UK, BG). Implement the logic to change the current `svelte-i18n` locale and persist the selected language in `localStorage`. Integrate this component into the header in the `+layout.svelte` file."
25. **Prompt 23 (Translations Integration):** "Update the previously created pages: `/login`, `/vehicles`, `/logs`, and Dashboard. Replace all hardcoded text strings (headers, table column names, button texts, notifications) with calls to the translation function `{$_('key')}`. Generate the corresponding keys and translations for the `en.json`, `ru.json`, `uk.json`, and `bg.json` files."

### Phase 7: DevOps & Manual Testing
26. **Prompt 24 (Camera Simulator):** "Write a standalone Python script (`simulator.py`) using the `requests` library. It should generate mock license plate strings and repeatedly send `multipart/form-data` POST requests to the local webhook endpoint every 10 seconds, including the configured webhook auth header."
27. **Prompt 25 (Dockerization):** "Write a `Dockerfile` for the FastAPI backend using `python:3.11-slim`. Write a separate multi-stage `Dockerfile` for the SvelteKit frontend using Node.js."
28. **Prompt 26 (Orchestration):** "Create a `docker-compose.yml` file. Define three services: `postgres:15`, `backend`, and `frontend`. Configure a shared Docker volume for the backend `/media` directory and expose media via backend static routes consumed by frontend URLs."
29. **Prompt 27 (Documentation):** "Generate a comprehensive `README.md`. Document the project structure, list all required environment variables, provide instructions for starting the system via Docker Compose, and include links to the Swagger API documentation."

### Phase 8: Automated Testing
30. **Prompt 28 (Backend Tests):** "Install `pytest`, `pytest-asyncio`, and `httpx`. Create a `backend/tests/` directory. Write asynchronous unit tests for the `/api/auth/login`, `/api/vehicles`, and webhook-auth validation behavior. Configure a temporary SQLite database for testing isolation."
31. **Prompt 29 (Frontend Tests):** "Install `vitest`, `jsdom`, and `@testing-library/svelte`. Create a `frontend/src/tests/` directory. Write unit tests for the `LanguageSwitcher.svelte` component to verify state changes, and for the `VehicleForm.svelte` component to verify regex validation logic."
32. **Prompt 30 (Stack & Data Flow Diagram):** "Generate a Mermaid.js diagram or a detailed text-based architecture map. It must show the flow of data: ANPR Camera -> FastAPI Webhook -> PostgreSQL (Metadata) & Local Disk (Images) -> SvelteKit Dashboard via REST/SSE. Include the 'Hardware Trigger' loop back to the Camera Relay."

**Phase 9: System Reliability & Maintenance**
33. **Prompt 31 (Cleanup Task):** "Write an asynchronous background service to delete images and database records older than X days (default 30). Ensure it safely handles file system operations to prevent 'file not found' errors."
34. **Prompt 32 (System Health Indicator):** "Implement a backend logic to track the timestamp of the last received webhook. Add a REST endpoint to return the system status. Create a small 'System Status' LED-style component in the SvelteKit Header (Green for online, Red for no heartbeat)."
35. **Prompt 33 (Logging & Debugging):** "Integrate the `loguru` library for structured logging. Ensure all camera requests, relay trigger attempts, and database errors are logged to both the console and a `logs/app.log` file with rotation."

### Phase 10: Post-MVP Security Hardening
36. **Prompt 34 (Webhook HMAC Hardening):** "Upgrade webhook authentication from static token to HMAC signature verification. Require headers `X-Webhook-Timestamp` and `X-Webhook-Signature`, compute HMAC-SHA256 over `timestamp + raw_body` using a shared secret, reject stale timestamps (e.g., older than 300 seconds), and use constant-time signature comparison. Keep backward compatibility behind a feature flag (`WEBHOOK_AUTH_MODE=token|hmac`) for gradual rollout. Add unit tests for valid signature, invalid signature, and replay/stale timestamp cases."

### Phase 11: Subscription / Time-Limited Access

> **Design rationale:** Records are never deleted on expiry — audit history is preserved. Instead, `valid_until` is a nullable UTC datetime on `Vehicle`. A `null` value means permanent access (fully backward-compatible). The expiry worker periodically transitions expired-but-still-`allowed` vehicles to `blocked` and emits a security audit event. This is simpler than a separate `Subscription` model and avoids status enum proliferation.

37. **Prompt 35 (Subscription DB Migration):** "Add two nullable UTC datetime columns to the `vehicles` table: `valid_from` (datetime, nullable, default NULL) and `valid_until` (datetime, nullable, default NULL, indexed). Generate an Alembic migration. Existing rows must receive NULL for both columns. Update the `Vehicle` SQLAlchemy model and the `VehicleCreate`/`VehicleUpdate`/`VehicleOut` Pydantic schemas to include these fields (both optional, ISO-8601 format with `Z`)."

38. **Prompt 36 (Subscription Access Check):** "Update `crud/vehicle.py` — `get_vehicle_by_plate()` access check: a vehicle grants access only when `status == 'allowed'` AND (`valid_until IS NULL` OR `valid_until > UTC now`). Add an async CRUD helper `get_expiring_soon(db, within_days: int)` that returns vehicles where `valid_until` is between now and now+N days and status is still `allowed`. Add unit tests: active subscription grants access; expired subscription (valid_until in the past) denies access; null valid_until vehicle is unaffected."

39. **Prompt 37 (Subscription Expiry Worker):** "Add an async background task `subscription_expiry_worker` (similar in structure to the existing relay worker) that runs on a configurable interval (`SUBSCRIPTION_EXPIRY_CHECK_INTERVAL_SECONDS`, default 3600). The task queries vehicles where `valid_until < UTC now` and `status == 'allowed'`, sets their status to `blocked`, and emits a `security_audit` event `subscription_expired` with `plate_number` and `valid_until` in details. The task must be idempotent and safe to run concurrently. Register it in `main.py` startup. Add unit tests for single expiry, batch expiry, and no-op when no vehicles are due."

40. **Prompt 38 (Subscription UI & Stats):** "(a) Backend: extend `GET /api/stats` response to include `active_subscriptions` (vehicles with non-null `valid_until >= now` and `status=allowed`) and `expiring_soon_count` (vehicles with `valid_until` within 7 days). Add optional query param `subscription` to `GET /api/vehicles` accepting values `all` (default) | `active` | `expiring_soon` | `expired` | `permanent`. (b) Frontend: update the Vehicle form modal — add optional `valid_from` date input and `valid_until` date input (date picker, UTC). In the vehicles table add a `Valid Until` column showing a badge: green (active), amber (≤7 days), red (expired), grey (permanent). Add two new stat widgets to the Dashboard for `active_subscriptions` and `expiring_soon_count`. Add i18n keys for all new strings in all four locale files."

### Phase 12: Real-Time Monitoring & Observability

> **Design rationale:** The camera sends `direction` (approach/leave) in the ITSAPI payload, enabling a live occupancy counter without separate hardware. Grafana re-uses the already-deployed `/metrics` Prometheus endpoint. RTSP streaming is optional and requires an external media proxy — kept separate to avoid bloating the core stack.

41. **Prompt 39 (Occupancy Counter):** "Add a new in-memory counter `OccupancyTracker` in `backend/core/occupancy.py` with two operations: `enter()` and `leave()`, both thread-safe (asyncio.Lock). Expose `GET /api/occupancy` returning `{\"current\": int, \"updated_at\": ISO-8601}`. Update `handle_anpr_webhook` in `backend/api/webhook.py` to call `enter()` when `direction` field equals `approach` (or its camera aliases) and `leave()` when `direction` equals `leave`; ignore if field is absent (backward-compatible). Persist the counter across restarts using a single-row `occupancy` table in PostgreSQL (upsert on startup load + write-through on change). Add a `/api/occupancy/stream` SSE endpoint that pushes the current count whenever it changes. Add unit tests for enter/leave logic, counter floor at 0, and missing direction field."

42. **Prompt 40 (Live Event Ticker):** "Add a `GET /api/events/live` SSE endpoint that replays the last 20 `AccessLog` entries on connect and then pushes each new entry as a JSON event as it is created (re-use the existing in-process SSE broadcast mechanism). Create a `LiveTicker.svelte` component that connects to this stream and renders a scrolling list of events: plate number, direction badge (→ / ←), access decision chip (green/red), thumbnail (if image_path available), and elapsed time. Mount the component in the Dashboard sidebar column. Add i18n keys for all new strings. Add a Vitest unit test that verifies the component renders an initial list and prepends new events."

43. **Prompt 41 (Grafana Compose Profile):** "Add a `grafana` Docker Compose profile to `docker-compose.yml` activated via `--profile monitoring`. Include two services: `prometheus` (scrapes `/metrics` on backend) and `grafana` (pre-provisioned datasource + dashboard JSON). The dashboard must include panels for: webhook events/min, allowed vs. denied ratio, relay success ratio, webhook p95 latency, current occupancy, and queue depth. Store provisioning configs under `docker/grafana/`. Do not affect the default compose profile. Document activation in `README.md`."

44. **Prompt 42 (Camera RTSP Proxy — optional):** "Add an optional `mediamtx` (formerly rtsp-simple-server) service to docker-compose under `--profile streaming`. Configure it to re-stream the camera RTSP feed (`rtsp://CAMERA_IP/cam/realmonitor`) as HLS at `/hls/camera.m3u8`. Add a `CameraFeed.svelte` component using an `<video>` HLS.js player embedded in the Dashboard. Add `CAMERA_RTSP_URL` to `.env.example` with a safe default of `disabled`. The component must gracefully hide itself when the URL is not configured."

---

## Plan Execution Status (2026-04-29)

- [x] Prompt 0: Root setup
- [~] Prompt 0.5.1-0.5.6: Governance exists in docs, but prompt-level one-commit policy was not followed historically 1:1
- [x] Prompt 0.5.7: `.env.example` maintained with required variables and defaults
- [x] Prompt 0.5.8: `scripts/check-all.sh` present and documented
- [x] Prompt 1: FastAPI async DB settings + CORS from env
- [x] Prompt 2: Models implemented
- [x] Prompt 2 (migration): Alembic scaffold + initial migration added under `backend/alembic`
- [x] Prompt 3: JWT + password hashing
- [x] Prompt 4: Auth endpoint + admin seed
- [x] Prompt 5: Vehicle CRUD with pagination
- [x] Prompt 6: Multipart webhook + async media save
- [x] Prompt 7: Access logic and logging
- [x] Prompt 8: Relay integration
- [x] Prompt 9: Logs API + static media mount
- [x] Prompt 10: Stats API
- [x] Prompt 11: SSE stream
- [x] Prompt 11.1: Manual relay trigger
- [x] Prompt 12-23: Frontend setup, auth, pages, logs, CSV, image modal, SSE, i18n
- [x] Prompt 24: `simulator.py`
- [x] Prompt 25: Backend and frontend Dockerfiles
- [x] Prompt 26: `docker-compose.yml`
- [x] Prompt 27: `README.md`
- [x] Prompt 28-29: Backend and frontend tests
- [x] Prompt 30: Data-flow diagram added in `docs/data-flow.mmd`
- [x] Prompt 31-33: Cleanup service, system status indicator, structured logging
- [x] Prompt 34: HMAC hardening with token/hmac mode switch and tests

### Final Done Marker

- Date: 2026-04-29
- Baseline completion commit: `262fa11`
- Post-hardening/operations commit: `812f264`
- Status: MVP + reliability + security hardening complete for local and compose environments

## Expansion Wave (2026-04-30)

### Implemented in this wave

- [x] RBAC baseline (`admin`, `operator`, `viewer`) with route-level enforcement
- [x] Security audit events for login, manual relay trigger, and duplicate webhook detection
- [x] Webhook idempotency via `X-Event-Id`/body hash dedup (`webhook_events` table)
- [x] Broader sensitive-endpoint rate limiting controls (`SENSITIVE_RATE_LIMIT`)
- [x] Frontend browser E2E smoke via Playwright
- [x] CI security lanes: Bandit (SAST), pip-audit, pnpm audit, ZAP baseline (DAST, non-blocking)
- [x] Observability baseline: Prometheus metrics endpoint (`/metrics`)
- [x] Docker backend runtime env parametrization (`BACKEND_HOST`, `BACKEND_PORT`, compose wiring)
- [x] Controlled DAST gate behavior: infrastructure/report generation failures now fail CI; alert severity remains policy-driven
- [x] PostgreSQL backup/restore automation scripts for compose runtime (`scripts/backup-postgres.sh`, `scripts/restore-postgres.sh`)
- [x] Production runbook baseline added (`docs/runbook-production.md`)
- [x] SLO/alerting baseline added (`docs/slo-alerting-baseline.md`)
- [x] Critical flow smoke script added (`scripts/smoke-critical-flow.sh`) for allowed/blocked webhook decisions
- [x] Relay queue/worker added with retry and dead-letter states (`relay_jobs` table + background worker)

### Contracts and change policy

1. API compatibility:
  - non-breaking additions are allowed in minor versions (`vX.Y.0`)
  - removals/behavioral breaks require major version bump and migration notes
2. DB migration policy:
  - every schema change ships with Alembic migration
  - destructive migrations require explicit operator approval and rollback plan
3. Rollback policy:
  - keep N-1 image available
  - migration compatibility must allow one-version rollback window where feasible

### Planned next slices (not yet implemented)

1. ~~Queue/worker isolation for heavy integrations (camera retries, relay retry queue)~~ ✅ relay_jobs + worker implemented in Expansion Wave
2. ~~Automated backup/restore jobs for Postgres + periodic restore validation in staging~~ ✅ `scripts/validate-backup.sh` + `backup-validation` CI job (2026-04-30)
3. ~~Production profile hardening (strict CSP, mTLS/internal auth between services, secret manager)~~ ✅ CSP tightened (`object-src 'none'`, `base-uri`, `form-action`), Vault adapter `core/secrets.py` (2026-04-30)
4. ~~Advanced test families: contract/load/chaos/property/migration tests in CI matrix~~ ✅ `test_api_contract.py`, `test_migrations.py`, `test_property.py` (Hypothesis), `locustfile.py`, `migration-tests` + `load-test-smoke` + `backup-validation` CI jobs (2026-04-30)
5. ~~Media storage strategy options in production~~ ✅ `core/storage.py` — LocalStorage / S3Storage abstraction, MinIO profile in docker-compose (2026-04-30)

### Remaining / future work

- mTLS between backend and internal services
- Chaos/fault-injection tests (e.g. Toxiproxy)
- Encrypted block storage with retention classes
- Staging environment auto-deploy pipeline
- ~~**[TODO — camera] Plate field name normalization:** Dahua ITC413 sends `plateNumber` (camelCase); add field alias or normalization layer in `backend/api/webhook.py` to accept both `plate_number` and `plateNumber`~~ ✅ `form.get("plate_number") or form.get("plateNumber")` + `SIM_DAHUA_MODE` in `simulator.py` (2026-04-30)
- **[TODO — camera] Webhook auth mode `basic`:** Dahua HTTP event notifications use Basic Auth, not `X-Webhook-Token`; add `WEBHOOK_AUTH_MODE=basic` support or document camera-side custom header configuration
- ~~**[TODO — camera] Image field name:** confirm whether camera firmware sends `image` or `plateImage`; update webhook to accept both or align with confirmed field name~~ ✅ `form.get("image") or form.get("plateImage")` — webhook now accepts both (2026-04-30)
- **[TODO — camera] Relay strategy:** evaluate replacing external `trigger_relay()` HTTP POST with Dahua CGI command (`/cgi-bin/accessControl.cgi`) using the camera's built-in Digital Output; document decision and implement if chosen
- **[TODO — camera] Additional metadata fields:** Dahua payload may include `channelName`, `dateTime`, `country`, `plateColor`, `vehicleColor`, `direction`; decide whether to store or log these for audit purposes
- **[TODO — subscriptions] Prompt 35:** DB migration — add `valid_from` / `valid_until` nullable columns to `vehicles`, update model + schemas
- **[TODO — subscriptions] Prompt 36:** Access check — deny if `valid_until` is in the past; add `get_expiring_soon()` CRUD helper + unit tests
- **[TODO — subscriptions] Prompt 37:** Expiry worker — background task marks expired vehicles as `blocked`, emits audit event `subscription_expired`
- **[TODO — subscriptions] Prompt 38:** Frontend + Stats — vehicle form date pickers, table expiry badge, dashboard widgets, i18n keys
- **[TODO — monitoring] Prompt 39:** Occupancy counter — `direction` field → enter/leave, `/api/occupancy` REST + SSE, PostgreSQL persistence, unit tests
- **[TODO — monitoring] Prompt 40:** Live event ticker — `/api/events/live` SSE, `LiveTicker.svelte` component on Dashboard with plate/direction/decision/thumbnail, i18n, Vitest test
- **[TODO — monitoring] Prompt 41:** Grafana compose profile — Prometheus + Grafana with pre-provisioned dashboard (webhook rate, occupancy, relay ratio, latency, queue depth)
- **[TODO — monitoring] Prompt 42 (optional):** RTSP proxy — `mediamtx` compose service + `CameraFeed.svelte` HLS player, `--profile streaming`, graceful disable when `CAMERA_RTSP_URL` not set
- **[TODO — audit] Audit log viewer:** таблиця `security_audit_events` існує в БД, але відсутня сторінка в UI для перегляду адміністратором; додати `/admin/audit` з фільтрами за датою, типом події, plate
- **[TODO — reporting] Reports / Звіти:** PDF або Excel звіт за місяць — кількість в'їздів per vehicle, погодинна статистика, топ-10 активних номерів; зараз є тільки CSV логів
- **[TODO — reliability] Webhook retry metrics:** ITC413 повторює надсилання при помилці; ідемпотентність через `X-Event-Id` є, але відсутня метрика retry-count та алерт при аномальному зростанні повторів
- **[TODO — reliability] Graceful shutdown:** при зупинці контейнера `relay_worker` і `cleanup_task` можуть перерватися на середині; додати SIGTERM handler з drain (завершити поточне завдання, відмовити нові)
- **[TODO — observability] DB connection pool monitoring:** відсутня метрика активних з'єднань SQLAlchemy; додати `pool_size`, `checked_out`, `overflow` до Prometheus endpoint

### Future features (low priority — implement on demand only)

- **[future] Notifications:** SMS / email / Telegram при відхиленні невідомого номера, за 7 днів до закінчення абонементу, при відключенні камери
- **[future] Multi-camera / multi-site:** прив'язка `camera_id` / `location` до подій; зараз система монолітна (1 камера + 1 relay), `channelName` з ITSAPI вже надходить і може слугувати ідентифікатором
- **[future] Bulk import/export vehicles:** CSV import для завантаження сотень номерів одразу; критично для великих паркінгів
- **[future] Telegram bot / mobile interface:** швидкий доступ оператора без браузера — підтвердити, відхилити, відкрити шлагбаум вручну

---

## Deployment Plan (Proposed)

### Stage 1: Pre-deploy gates

1. Run local gate: `./scripts/check-all.sh`
2. Run smoke checks: `npm run doctor` and `npm run smoke`
3. Ensure secrets are non-default (`APP_ENV=production` blocks weak defaults)

### Stage 2: Build and artifact strategy

1. Build backend image from `backend/Dockerfile`
2. Build frontend image from `frontend/Dockerfile` with `VITE_API_BASE_URL` build arg
3. Tag images with immutable version (`vX.Y.Z`) and commit SHA

### Stage 3: Environment promotion

1. Dev -> Staging -> Production promotion using the same image artifacts
2. Apply DB migrations with Alembic before backend rollout:
  - `python -m alembic -c backend/alembic.ini upgrade head`
3. Roll backend first, then frontend

### Stage 4: Runtime verification

1. Health probe: `/health`
2. Auth smoke: `/api/auth/login`, `/api/auth/me`
3. Business smoke: `/api/system/status`, `/api/stats`, `/api/logs`
4. CORS probe for expected origin

### Stage 5: Rollback strategy

1. Keep previous image tag available
2. Roll back application image first
3. If migration introduced incompatible changes, maintain backward-compatible migrations or explicit down migration plan

---

## Security & Accuracy Verification Plan

### Security checks

1. Secrets policy:
  - enforce strong values for `SECRET_KEY`, `ADMIN_PASSWORD`, `WEBHOOK_SHARED_SECRET`, and `WEBHOOK_HMAC_SECRET` (when HMAC mode)
2. Webhook hardening:
  - prefer `WEBHOOK_AUTH_MODE=hmac` in production
  - monitor failed signature and stale timestamp rates
3. Input hardening:
  - allow only image/jpeg, image/png, image/webp
  - enforce `WEBHOOK_MAX_IMAGE_BYTES`
4. Transport and infra:
  - terminate TLS at ingress/reverse proxy
  - restrict backend exposure to trusted networks
5. Access control:
  - verify all admin routes require auth
  - validate CORS origin policy before release

### Accuracy/reliability checks

1. Data correctness:
  - validate plate normalization and access decision consistency
2. Time semantics:
  - confirm UTC timestamps (`Z`) in APIs and logs
3. Regression guardrails:
  - backend unit tests + frontend unit tests + smoke checks in CI
4. Operational visibility:
  - monitor webhook receive rate, deny ratio, relay success/failure rate
5. Periodic audits:
  - weekly review of auth failures, relay timeouts, and cleanup behavior

---

## Real-World Emulation Options

1. Synthetic webhook traffic (already available):
  - use `simulator.py` for periodic multipart events
2. Burst/load simulation:
  - run parallel simulator instances with varied intervals and payload sizes
3. Data quality simulation:
  - mix valid/invalid plates, malformed files, unsupported content types
4. Security scenario simulation:
  - replay old HMAC timestamp payloads
  - send invalid signatures and verify rejection/monitoring
5. Hardware fault simulation:
  - point relay endpoint to timeout/non-2xx mock and validate graceful degradation
6. End-to-end operational drills:
  - run `npm run doctor` and `npm run smoke` before and after releases

---

## MVP to Product Roadmap

### Priority 1: Product Readiness (Must-Have)

1. Reliability of event processing:
  - isolate heavy/slow operations from request path
  - define target throughput and backlog limits
2. Queue/worker architecture:
  - move retry-capable integration tasks to worker queue
  - add dead-letter handling for repeatedly failing tasks
3. End-to-end idempotency:
  - enforce dedup and replay-safety on all critical integration paths
4. Service Level Objectives (SLO):
  - set availability target for API and webhook processing
  - set latency and success-rate targets for access decisions

### Priority 2: Production Security

1. Dependency security policy:
  - remove temporary audit ignores as soon as patched versions are available in package index
2. Secrets management:
  - use managed secrets store and periodic secret rotation
  - separate staging and production secret scopes
3. RBAC hardening:
  - map business roles to business operations explicitly
  - enforce least-privilege access in admin flows
4. Security gates in CI:
  - enforce blocking behavior for high/critical findings where patch path exists

### Priority 3: Operations and Recovery

1. Backup and restore:
  - schedule automated backups for PostgreSQL and media metadata
  - run regular restore verification in staging
2. Incident runbooks:
  - prepare documented response for camera outage, relay outage, DB degradation, and auth failures
3. Monitoring and alerting:
  - alert on latency, error rate, queue depth, webhook throughput drops, and relay failure spikes
4. Staging parity:
  - maintain production-like staging environment for pre-release validation

### Priority 4: Release Quality and Change Safety

1. Contract tests:
  - enforce API contract compatibility between frontend and backend
2. Critical-path E2E:
  - verify allowed plate opens gate
  - verify blocked plate denies and never triggers relay
3. Migration safety:
  - require migration dry-run and rollback plan validation in staging
4. Controlled rollout:
  - add feature flags and progressive rollout for risky changes

## Next Sprint (Highest ROI)

1. Implement queue/worker with retry policy and dead-letter queue
2. Add nightly restore verification in CI/staging using existing backup/restore scripts
3. Tighten security job policy for actionable high/critical findings
4. Integrate runbook/SLO checks into operational review cadence and alert routing
5. Expand E2E suite to full happy-path and deny-path with relay side-effect verification
6. **[camera] Resolve Dahua ITC413-PW4D-IZ1 field mapping and auth mode** (see Hardware Integration section)
7. **[camera] Confirm image field name and relay strategy against real firmware**
8. **[subscriptions] Implement Phase 11 (Prompts 35–38): time-limited access / subscription passes** — start with DB migration (Prompt 35)
9. **[monitoring] Implement Phase 12 (Prompts 39–42): real-time monitoring** — start with occupancy counter (Prompt 39), highest ROI items: Prompt 39 + 40 + 41

## Product Readiness Exit Criteria

1. 30 consecutive days of stable staging operation without critical incidents
2. Backup restore validated within target RTO/RPO
3. CI quality gates and security checks stable and green
4. System load profile meets target throughput and latency
5. On-call/operator can complete incident runbook steps without developer intervention

---

## Hardware Integration: Dahua ITC413-PW4D-IZ1

### Camera specifications

| Parameter | Value |
|-----------|-------|
| **Model** | Dahua ITC413-PW4D-IZ1 |
| **Sensor** | 1/1.8" CMOS, 4 MP (2688×1520) |
| **Lens** | Motorized varifocal 2.7–12 mm, F1.4, auto DC iris |
| **Field of view** | H: 92°–46.1° / V: 49°–26° |
| **IR illumination** | 850 nm, 4 sources; 10 m (plate recognition), 30 m (surveillance) |
| **Detection speed** | up to 80 km/h |
| **Sensitivity** | 0.001 lux (color), 0.0002 lux (B/W), 0 lux (IR) |
| **WDR** | 140 dB |
| **Encoding** | H.265+/H.264+/H.265/H.264/MJPEG |
| **RAM / ROM** | 1 GB / 4 GB |
| **Storage** | MicroSD up to 256 GB |
| **Network** | RJ-45 10/100/1000 Mbps |
| **Power** | 12 V DC 2 A or PoE 802.3at (≤20 W) |
| **Protection** | IP67, IK10 |
| **Operating temp** | −30°C to +65°C |
| **Dimensions** | 396 × 120.8 × 127.8 mm, 2.3 kg |
| **Certifications** | CE-EMC, CE-LVD, CE-RED, FCC |

#### I/O interfaces

| Interface | Details |
|-----------|---------|
| **Alarm inputs** | 2 (opto-isolated, 5 V threshold) |
| **Alarm outputs (relay DO)** | 2 relays — 30 V DC / 0.5 A, 50 V AC / 500 mA |
| **RS-485** | 2 (half-duplex, pass-through, DHRS, data output) |
| **Wiegand** | 1 (SHA-1, 26-bit) |
| **Audio in/out** | Built-in mic (3 m, 48 kHz), 2 W speaker, 1× RCA out |
| **Remote control** | 433 / 868 MHz, range 15 m (line-of-sight) |

#### ANPR intelligence

| Feature | Value |
|---------|-------|
| **Plate recognition rate** | ≥96% (front/rear); ≥98% (EU plates) |
| **Vehicle detection rate** | ≥99% (recommended installation conditions) |
| **Vehicle types** | 9 (sedan, SUV, bus, heavy/medium/light truck, van, minivan, pickup) |
| **Vehicle colors** | 12 |
| **Brand logos** | 147 |
| **Plate regions** | EU, CIS/Ukraine/Russia, Arabic, Latin America, North America + optional Asia/Africa |
| **Whitelist / Blacklist** | 110 000 entries each (on-camera) |
| **Protocols** | ONVIF (S, G, T), CGI, **ITSAPI**, P2P, HTTP/HTTPS, FTP, SMTP, SNMP |
| **SDK / API** | Yes (Dahua SDK + CGI HTTP API) |

#### Key integration notes for this project

- **On-camera whitelist/blacklist (110k entries each):** camera can make access decisions autonomously; this project centralises all decisions in the FastAPI backend instead — camera acts as a pure sensor.
- **ITSAPI** is the primary protocol for ANPR event delivery over HTTP; the camera pushes `multipart/form-data` notifications to a configured URL.
- **Relay DO outputs (2×):** direct hardware relay to barrier/gate. Can be triggered by: (a) on-camera logic, (b) CGI command `POST /cgi-bin/accessControl.cgi` from backend, or (c) remote-control receiver (433/868 MHz).
- **RS-485 / Wiegand:** alternative paths for access controller integration (not used in this project currently).
- **MicroSD on-board:** camera can store snapshots and video locally as fallback if network to backend is lost.

### Integration gap analysis (2026-04-30)

| # | Area | Current implementation | Camera behavior | Action required |
|---|------|----------------------|-----------------|-----------------|
| 1 | Plate field name | `plate_number` (snake_case) | `plateNumber` (camelCase via ITSAPI) | ✅ Done — `form.get("plate_number") or form.get("plateNumber")` |
| 2 | Image field name | `image` | `plateImage` (ITSAPI standard) | ✅ Done — `form.get("image") or form.get("plateImage")` |
| 3 | Webhook auth | `X-Webhook-Token` header | HTTP Basic Auth (ITSAPI) or Digest Auth | Pending — add `WEBHOOK_AUTH_MODE=basic` or configure custom header on camera |
| 4 | Relay trigger | External HTTP POST to `RELAY_IP` | Built-in DO relay (hardware) or Dahua CGI API | Pending — evaluate `POST /cgi-bin/accessControl.cgi` vs. separate relay endpoint |
| 5 | Extra metadata | Ignored | `channelName`, `dateTime`, `country`, `plateColor`, `vehicleColor`, `direction` | Decide: log only or store for audit |

### Additional metadata fields sent by camera (ITSAPI payload)

Dahua ITC cameras send the following fields in the `multipart/form-data` ITSAPI notification alongside the plate number and image:

- `plateNumber` — recognised plate string
- `plateImage` — JPEG snapshot of the plate crop
- `channelName` — camera channel label
- `dateTime` — camera-local timestamp (ISO-8601)
- `country` — plate country/region code
- `plateColor` — plate background colour
- `vehicleColor` — vehicle body colour
- `vehicleType` — vehicle type category
- `vehicleBrand` — recognised brand/logo
- `direction` — travel direction (approach/leave)
- `speed` — detected speed (km/h, if speed detection enabled)

These are currently ignored by the webhook — store or log if needed for audit purposes.

### Implementation order

1. ✅ Resolve field name mapping (`plateNumber`, `plateImage`) — done
2. Resolve auth mode (ITSAPI Basic Auth vs. custom header)
3. Relay strategy decision (hardware DO direct-wire vs. CGI API command)
4. Decision on extra metadata fields (log-only vs. store in DB)
