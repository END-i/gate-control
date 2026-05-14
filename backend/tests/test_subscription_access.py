"""Unit tests for Prompt 36: subscription access check in get_vehicle_by_plate."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from crud.vehicle import get_expiring_soon, get_vehicle_by_plate
from models.vehicle import Vehicle, VehicleStatus


def _utc(**delta) -> datetime:
    return datetime.now(timezone.utc) + timedelta(**delta)


async def _add(db_session, plate: str, status: VehicleStatus, **kwargs) -> Vehicle:
    v = Vehicle(license_plate=plate, status=status, **kwargs)
    db_session.add(v)
    await db_session.commit()
    await db_session.refresh(v)
    return v


# ---------------------------------------------------------------------------
# Active subscription grants access
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_active_subscription_grants_access(db_session):
    await _add(
        db_session, "SUB001", VehicleStatus.ALLOWED,
        valid_from=_utc(days=-10),
        valid_until=_utc(days=30),
    )
    result = await get_vehicle_by_plate(db_session, "SUB001")
    assert result is not None
    assert result.status == VehicleStatus.ALLOWED


# ---------------------------------------------------------------------------
# Expired subscription denies access (returns None)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_expired_subscription_denies_access(db_session):
    await _add(
        db_session, "SUB002", VehicleStatus.ALLOWED,
        valid_until=_utc(days=-1),
    )
    result = await get_vehicle_by_plate(db_session, "SUB002")
    assert result is None


# ---------------------------------------------------------------------------
# valid_from in the future means subscription not yet started (returns None)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_subscription_not_yet_started_denies_access(db_session):
    await _add(
        db_session, "SUB003", VehicleStatus.ALLOWED,
        valid_from=_utc(days=5),
        valid_until=_utc(days=30),
    )
    result = await get_vehicle_by_plate(db_session, "SUB003")
    assert result is None


# ---------------------------------------------------------------------------
# NULL valid_until is treated as permanent — unaffected by subscription logic
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_null_valid_until_is_permanent(db_session):
    await _add(db_session, "SUB004", VehicleStatus.ALLOWED)
    result = await get_vehicle_by_plate(db_session, "SUB004")
    assert result is not None


# ---------------------------------------------------------------------------
# Blocked vehicle is returned as-is (caller decides on denial)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_blocked_vehicle_returned_for_status_check(db_session):
    await _add(db_session, "SUB005", VehicleStatus.BLOCKED)
    result = await get_vehicle_by_plate(db_session, "SUB005")
    assert result is not None
    assert result.status == VehicleStatus.BLOCKED


# ---------------------------------------------------------------------------
# get_expiring_soon returns vehicles expiring within N days
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_expiring_soon_returns_near_expiry(db_session):
    await _add(db_session, "EXP001", VehicleStatus.ALLOWED, valid_until=_utc(days=3))
    await _add(db_session, "EXP002", VehicleStatus.ALLOWED, valid_until=_utc(days=10))
    result = await get_expiring_soon(db_session, within_days=7)
    plates = {v.license_plate for v in result}
    assert "EXP001" in plates
    assert "EXP002" not in plates


@pytest.mark.asyncio
async def test_get_expiring_soon_excludes_already_expired(db_session):
    await _add(db_session, "EXP003", VehicleStatus.ALLOWED, valid_until=_utc(days=-1))
    result = await get_expiring_soon(db_session, within_days=7)
    assert not any(v.license_plate == "EXP003" for v in result)


@pytest.mark.asyncio
async def test_get_expiring_soon_excludes_blocked_vehicles(db_session):
    await _add(db_session, "EXP004", VehicleStatus.BLOCKED, valid_until=_utc(days=3))
    result = await get_expiring_soon(db_session, within_days=7)
    assert not any(v.license_plate == "EXP004" for v in result)
