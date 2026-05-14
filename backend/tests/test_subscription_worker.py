"""Unit tests for Prompt 37: subscription expiry worker."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from core.subscription_worker import _check_and_expire
from models.vehicle import Vehicle, VehicleStatus


def _utc(**delta) -> datetime:
    return datetime.now(timezone.utc) + timedelta(**delta)


def _make_factory(db_session):
    """Build an async_sessionmaker that connects to the same SQLite file as db_session."""
    url = str(db_session.sync_session.get_bind().url)
    engine = create_async_engine(url)
    return async_sessionmaker(bind=engine, expire_on_commit=False)


async def _add(db_session, plate: str, status: VehicleStatus, **kwargs) -> Vehicle:
    v = Vehicle(license_plate=plate, status=status, **kwargs)
    db_session.add(v)
    await db_session.commit()
    await db_session.refresh(v)
    return v


# ---------------------------------------------------------------------------
# Single expiry
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_single_expired_vehicle_is_blocked(db_session, monkeypatch):
    """A single expired allowed vehicle must be set to BLOCKED."""
    from core import subscription_worker

    monkeypatch.setattr(subscription_worker, "SessionLocal", _make_factory(db_session))

    await _add(db_session, "EXP_W01", VehicleStatus.ALLOWED, valid_until=_utc(days=-1))

    count = await _check_and_expire()
    assert count == 1

    db_session.expire_all()
    result = await db_session.execute(select(Vehicle).where(Vehicle.license_plate == "EXP_W01"))
    v = result.scalar_one()
    assert v.status == VehicleStatus.BLOCKED


# ---------------------------------------------------------------------------
# Batch expiry
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_batch_expiry(db_session, monkeypatch):
    from core import subscription_worker

    monkeypatch.setattr(subscription_worker, "SessionLocal", _make_factory(db_session))

    for i in range(3):
        await _add(
            db_session, f"BATCH_W{i:02d}", VehicleStatus.ALLOWED, valid_until=_utc(days=-i - 1)
        )

    count = await _check_and_expire()
    assert count == 3

    db_session.expire_all()
    result = await db_session.execute(
        select(Vehicle).where(Vehicle.license_plate.like("BATCH_W%"))
    )
    for v in result.scalars().all():
        assert v.status == VehicleStatus.BLOCKED


# ---------------------------------------------------------------------------
# No-op when nothing is due
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_no_op_when_nothing_due(db_session, monkeypatch):
    from core import subscription_worker

    monkeypatch.setattr(subscription_worker, "SessionLocal", _make_factory(db_session))

    await _add(db_session, "NOOP_W01", VehicleStatus.ALLOWED, valid_until=_utc(days=30))
    await _add(db_session, "NOOP_W02", VehicleStatus.BLOCKED, valid_until=_utc(days=-1))

    count = await _check_and_expire()
    assert count == 0

