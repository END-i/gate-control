# Stack and Data Flow Diagram

```mermaid
flowchart LR
    A[ANPR Camera] -->|multipart webhook| B[FastAPI /api/webhook/anpr]
    B -->|metadata| C[(PostgreSQL)]
    B -->|image files| D[(Local Disk media)]

    E[SvelteKit Dashboard] -->|REST| B
    E -->|SSE /api/logs/stream| B

    B -->|serve /media/*| E

    B -->|trigger_relay() HTTP POST| F[Camera Relay Endpoint]
    F -->|hardware action| A
```

## Components

- Backend: FastAPI + SQLAlchemy async + PostgreSQL
- Frontend: SvelteKit Node adapter + Tailwind CSS + svelte-i18n
- Real-time: Server-Sent Events for logs stream
- Storage split:
  - PostgreSQL for auth, vehicles, and access metadata
  - Local disk volume for image artifacts under media/YYYY/MM/DD/
