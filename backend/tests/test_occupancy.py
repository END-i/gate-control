"""Unit tests for Prompt 39: Occupancy Counter."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from core.occupancy import OccupancyTracker, _ENTER_DIRECTIONS, _LEAVE_DIRECTIONS
from models.occupancy import OccupancyState


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fresh() -> OccupancyTracker:
    """Return a new tracker instance (avoids polluting the module singleton)."""
    return OccupancyTracker()


# ---------------------------------------------------------------------------
# enter / leave
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_enter_increments(db_session):
    t = _fresh()
    await t.enter(db_session)
    assert t.snapshot()["current"] == 1
    await t.enter(db_session)
    assert t.snapshot()["current"] == 2


@pytest.mark.asyncio
async def test_leave_decrements(db_session):
    t = _fresh()
    await t.enter(db_session)
    await t.enter(db_session)
    await t.leave(db_session)
    assert t.snapshot()["current"] == 1


@pytest.mark.asyncio
async def test_leave_floors_at_zero(db_session):
    t = _fresh()
    await t.leave(db_session)  # nothing to leave
    assert t.snapshot()["current"] == 0


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_enter_persists_to_db(db_session):
    t = _fresh()
    await t.enter(db_session)

    result = await db_session.execute(select(OccupancyState).where(OccupancyState.id == 1))
    row = result.scalar_one()
    assert row.current_count == 1


@pytest.mark.asyncio
async def test_load_from_db_restores_state(db_session):
    # Seed a row directly
    row = OccupancyState(id=1, current_count=7, updated_at=datetime.now(timezone.utc))
    db_session.add(row)
    await db_session.commit()

    t = _fresh()
    await t.load_from_db(db_session)
    assert t.snapshot()["current"] == 7


@pytest.mark.asyncio
async def test_load_from_db_noop_when_empty(db_session):
    t = _fresh()
    await t.load_from_db(db_session)
    assert t.snapshot()["current"] == 0


# ---------------------------------------------------------------------------
# Snapshot shape
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_snapshot_shape(db_session):
    t = _fresh()
    snap = t.snapshot()
    assert "current" in snap
    assert "updated_at" in snap
    # updated_at should be a valid ISO-8601 string
    datetime.fromisoformat(snap["updated_at"])


# ---------------------------------------------------------------------------
# SSE pub/sub
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_subscriber_receives_enter_event(db_session):
    t = _fresh()
    q = await t.subscribe()
    await t.enter(db_session)
    snap = q.get_nowait()
    assert snap["current"] == 1


@pytest.mark.asyncio
async def test_unsubscribe_removes_queue(db_session):
    t = _fresh()
    q = await t.subscribe()
    t.unsubscribe(q)
    assert q not in t._subscribers


# ---------------------------------------------------------------------------
# Direction constants
# ---------------------------------------------------------------------------


def test_direction_constants():
    assert "approach" in _ENTER_DIRECTIONS
    assert "in" in _ENTER_DIRECTIONS
    assert "leave" in _LEAVE_DIRECTIONS
    assert "out" in _LEAVE_DIRECTIONS
