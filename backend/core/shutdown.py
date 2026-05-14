"""Graceful shutdown flag shared across background workers.

Workers should call ``is_shutting_down()`` in their loop and exit cleanly
(finishing the current unit of work) rather than being cancelled mid-flight.

The SIGTERM / SIGINT handlers call ``request_shutdown()`` which sets this flag.
The FastAPI lifespan ``finally`` block still cancels the asyncio tasks as a
safety net if the workers don't drain quickly enough.
"""
from __future__ import annotations

import asyncio
import signal
from typing import Optional

from loguru import logger

_shutdown_event: Optional[asyncio.Event] = None


def get_shutdown_event() -> asyncio.Event:
    """Return (and lazily create) the process-wide shutdown event."""
    global _shutdown_event
    if _shutdown_event is None:
        _shutdown_event = asyncio.Event()
    return _shutdown_event


def is_shutting_down() -> bool:
    """Return True once a shutdown has been requested."""
    return _shutdown_event is not None and _shutdown_event.is_set()


def request_shutdown() -> None:
    """Signal all workers to stop after finishing their current unit of work."""
    logger.info("Shutdown requested — draining workers")
    get_shutdown_event().set()


def install_signal_handlers() -> None:
    """Register SIGTERM and SIGINT handlers on the running event loop.

    No-op when called from a non-main thread (e.g. pytest workers).
    """
    import threading

    if threading.current_thread() is not threading.main_thread():
        return

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, request_shutdown)
    logger.debug("SIGTERM/SIGINT graceful-shutdown handlers installed")
