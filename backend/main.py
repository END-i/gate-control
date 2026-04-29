import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

from api.router import api_router
from core.cleanup import run_cleanup_service
from core.config import get_settings
from core.logging_config import configure_logging
from core.seed import seed_initial_admin

settings = get_settings()
cleanup_task: Optional[asyncio.Task[None]] = None
MEDIA_DIR = Path(__file__).resolve().parent / "media"


@asynccontextmanager
async def lifespan(_: FastAPI):
    global cleanup_task
    configure_logging()
    logger.info("Starting ANPR backend")
    skip_startup_tasks = os.getenv("ANPR_SKIP_STARTUP_TASKS") == "1"
    if not skip_startup_tasks:
        await seed_initial_admin()
        cleanup_task = asyncio.create_task(run_cleanup_service(days=30, interval_hours=24))
    try:
        yield
    finally:
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
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")

app.include_router(api_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
