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
