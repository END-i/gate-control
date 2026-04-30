"""Migration tests — verify that Alembic migrations apply and roll back
cleanly, and that the resulting schema matches the ORM models.

There are two layers of tests here:

1. **Schema structure tests** (SQLite, always run): create the full schema
   via ``Base.metadata.create_all()`` and assert that every expected table
   and key column exists.  These are fast, self-contained, and run in the
   normal ``quality-gate`` job.

2. **Alembic up/down cycle tests** (PostgreSQL, ``migration-tests`` CI job):
   run ``alembic upgrade head`` then ``alembic downgrade base`` against a
   real Postgres instance.  These are skipped unless the ``DATABASE_URL``
   env var points to a non-SQLite database.
"""
from __future__ import annotations

import os

import pytest
import pytest_asyncio
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_DB_URL = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
_IS_POSTGRES = _DB_URL.startswith("postgresql")


# ---------------------------------------------------------------------------
# Fixture: fresh engine per test (no shared state)
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture()
async def engine(tmp_path):
    if _IS_POSTGRES:
        url = _DB_URL
    else:
        url = f"sqlite+aiosqlite:///{tmp_path}/migrate_test.db"

    eng = create_async_engine(url, future=True)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture()
async def schema_engine(tmp_path):
    """Engine with the full ORM schema created via metadata (SQLite only)."""
    from models.base import Base  # noqa: PLC0415 — intentional lazy import
    # ensure all model modules are imported so metadata is populated
    import models.admin  # noqa: F401
    import models.vehicle  # noqa: F401
    import models.access_log  # noqa: F401

    url = f"sqlite+aiosqlite:///{tmp_path}/schema_test.db"
    eng = create_async_engine(url, future=True)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


# ---------------------------------------------------------------------------
# 1. Schema structure tests (SQLite, fast)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_admins_table_has_expected_columns(schema_engine):
    async with schema_engine.connect() as conn:
        columns = await conn.run_sync(
            lambda sync_conn: {
                col["name"] for col in inspect(sync_conn).get_columns("admins")
            }
        )
    assert {"id", "username", "hashed_password"} <= columns


@pytest.mark.asyncio
async def test_vehicles_table_has_expected_columns(schema_engine):
    async with schema_engine.connect() as conn:
        columns = await conn.run_sync(
            lambda sync_conn: {
                col["name"] for col in inspect(sync_conn).get_columns("vehicles")
            }
        )
    assert {"id", "license_plate", "status", "owner_info"} <= columns


@pytest.mark.asyncio
async def test_access_logs_table_has_expected_columns(schema_engine):
    async with schema_engine.connect() as conn:
        columns = await conn.run_sync(
            lambda sync_conn: {
                col["name"] for col in inspect(sync_conn).get_columns("access_logs")
            }
        )
    assert {"id", "license_plate", "timestamp", "access_granted", "image_path"} <= columns


@pytest.mark.asyncio
async def test_relay_jobs_table_has_expected_columns(schema_engine):
    async with schema_engine.connect() as conn:
        columns = await conn.run_sync(
            lambda sync_conn: {
                col["name"] for col in inspect(sync_conn).get_columns("relay_jobs")
            }
        )
    assert {
        "id", "event_type", "plate_number", "requested_by",
        "status", "attempt_count", "max_attempts", "last_error",
        "available_at", "created_at", "updated_at",
    } <= columns


@pytest.mark.asyncio
async def test_security_audits_table_has_expected_columns(schema_engine):
    async with schema_engine.connect() as conn:
        columns = await conn.run_sync(
            lambda sync_conn: {
                col["name"] for col in inspect(sync_conn).get_columns("security_audits")
            }
        )
    assert {"id", "event_type", "actor", "success", "details", "timestamp"} <= columns


@pytest.mark.asyncio
async def test_all_expected_tables_present(schema_engine):
    async with schema_engine.connect() as conn:
        tables = await conn.run_sync(
            lambda sync_conn: set(inspect(sync_conn).get_table_names())
        )
    expected = {
        "admins", "vehicles", "access_logs",
        "relay_jobs", "security_audits", "webhook_events",
    }
    assert expected <= tables


# ---------------------------------------------------------------------------
# 2. Alembic up / down cycle (PostgreSQL only — skipped on SQLite)
# ---------------------------------------------------------------------------

_skip_if_not_postgres = pytest.mark.skipif(
    not _IS_POSTGRES,
    reason="Alembic up/down tests require a PostgreSQL DATABASE_URL",
)


@_skip_if_not_postgres
def test_alembic_upgrade_head():
    """Apply all migrations to head — must succeed without errors."""
    import subprocess
    result = subprocess.run(
        ["python", "-m", "alembic", "-c", "alembic.ini", "upgrade", "head"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"alembic upgrade head failed:\n{result.stdout}\n{result.stderr}"
    )


@_skip_if_not_postgres
def test_alembic_downgrade_base():
    """Roll back all migrations to base — must succeed without errors."""
    import subprocess
    result = subprocess.run(
        ["python", "-m", "alembic", "-c", "alembic.ini", "downgrade", "base"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"alembic downgrade base failed:\n{result.stdout}\n{result.stderr}"
    )


@_skip_if_not_postgres
def test_alembic_upgrade_head_again():
    """Re-apply migrations after downgrade — idempotency check."""
    import subprocess
    result = subprocess.run(
        ["python", "-m", "alembic", "-c", "alembic.ini", "upgrade", "head"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"alembic upgrade head (second run) failed:\n{result.stdout}\n{result.stderr}"
    )


@_skip_if_not_postgres
@pytest.mark.asyncio
async def test_schema_matches_orm_after_migrations(engine):
    """After upgrade head, all ORM-defined tables must exist in the DB."""
    async with engine.connect() as conn:
        tables = await conn.run_sync(
            lambda sync_conn: set(inspect(sync_conn).get_table_names())
        )
    expected = {
        "admins", "vehicles", "access_logs",
        "relay_jobs", "security_audits", "webhook_events",
    }
    assert expected <= tables, f"Missing tables: {expected - tables}"
