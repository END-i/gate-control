"""Shared Prometheus metrics registry.

Metrics that need to be accessed from both the FastAPI app (main.py)
and sub-modules (api/, core/) are defined here to avoid circular imports.
"""
from __future__ import annotations

from prometheus_client import Counter, Gauge

# ---- Webhook metrics -------------------------------------------------------
WEBHOOK_DUPLICATE_TOTAL = Counter(
    "anpr_webhook_duplicate_total",
    "Total number of duplicate (already-seen) ANPR webhook events skipped",
)

# ---- DB connection pool metrics --------------------------------------------
DB_POOL_SIZE = Gauge("anpr_db_pool_size", "SQLAlchemy connection pool configured size")
DB_POOL_CHECKED_OUT = Gauge(
    "anpr_db_pool_checked_out", "SQLAlchemy connections currently checked out"
)
DB_POOL_OVERFLOW = Gauge(
    "anpr_db_pool_overflow", "SQLAlchemy connection pool overflow connections in use"
)
