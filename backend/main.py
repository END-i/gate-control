import asyncio
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import hmac

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from api.router import api_router
from core.cleanup import run_cleanup_service
from core.config import get_settings
from core.database import init_db
from core.logging_config import configure_logging
from core.relay_worker import run_relay_worker
from core.secrets import prefetch_secrets
from core.seed import seed_initial_admin

# Prefetch secrets from Vault (no-op when VAULT_ADDR is not set) so that
# pydantic-settings picks them up via os.environ before the first get_settings()
# call.
prefetch_secrets()

settings = get_settings()
cleanup_task: Optional[asyncio.Task[None]] = None
relay_worker_task: Optional[asyncio.Task[None]] = None
MEDIA_DIR = Path(__file__).resolve().parent / "media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)
HTTP_REQUESTS_TOTAL = Counter(
    "anpr_http_requests_total",
    "Total number of HTTP requests",
    ["method", "path", "status_code"],
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "anpr_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
)


def _validate_runtime_secrets() -> None:
    app_env = os.getenv("APP_ENV", "development").strip().lower()
    if app_env in {"dev", "development", "local", "test"}:
        return

    weak_keys: list[str] = []
    checks = {
        "SECRET_KEY": settings.secret_key,
        "ADMIN_PASSWORD": settings.admin_password,
        "WEBHOOK_SHARED_SECRET": settings.webhook_shared_secret,
    }
    if settings.webhook_auth_mode == "hmac":
        checks["WEBHOOK_HMAC_SECRET"] = settings.webhook_hmac_secret

    for key, value in checks.items():
        if not value or value.strip().lower() == "change-me":
            weak_keys.append(key)

    if weak_keys:
        raise RuntimeError(
            "Refusing to start with insecure defaults in non-development APP_ENV. "
            f"Set strong values for: {', '.join(weak_keys)}"
        )


def _localhost_origin_regex(frontend_url: str) -> Optional[str]:
    # If configured frontend is local dev, allow localhost/127.0.0.1 on any port.
    if frontend_url.startswith("http://localhost") or frontend_url.startswith("http://127.0.0.1"):
        return r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"
    return None


@asynccontextmanager
async def lifespan(_: FastAPI):
    global cleanup_task, relay_worker_task
    configure_logging()
    _validate_runtime_secrets()
    logger.info("Starting ANPR backend")
    skip_startup_tasks = os.getenv("ANPR_SKIP_STARTUP_TASKS") == "1"
    if not skip_startup_tasks:
        await init_db()
        await seed_initial_admin()
        cleanup_task = asyncio.create_task(run_cleanup_service(days=30, interval_hours=24))
        relay_worker_task = asyncio.create_task(run_relay_worker())
    try:
        yield
    finally:
        if relay_worker_task is not None:
            relay_worker_task.cancel()
            try:
                await relay_worker_task
            except asyncio.CancelledError:
                pass
            relay_worker_task = None
        if cleanup_task is not None:
            cleanup_task.cancel()
            try:
                await cleanup_task
            except asyncio.CancelledError:
                pass
            cleanup_task = None
        logger.info("Stopping ANPR backend")


app = FastAPI(title="ANPR Gate Control API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_origin_regex=_localhost_origin_regex(settings.frontend_url),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")

app.include_router(api_router)


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    started = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - started
    route_path = request.url.path
    HTTP_REQUESTS_TOTAL.labels(request.method, route_path, str(response.status_code)).inc()
    HTTP_REQUEST_DURATION_SECONDS.labels(request.method, route_path).observe(duration)

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "font-src 'self'; "
        "connect-src 'self'; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "form-action 'self'; "
        "frame-ancestors 'none';"
    )
    return response


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/metrics")
async def metrics(
    x_metrics_token: Optional[str] = Header(default=None, alias="X-Metrics-Token"),
) -> Response:
    api_key = settings.metrics_api_key
    if api_key and (
        x_metrics_token is None
        or not hmac.compare_digest(x_metrics_token, api_key)
    ):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
