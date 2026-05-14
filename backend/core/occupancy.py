from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

# Direction aliases recognised as "entering"
_ENTER_DIRECTIONS = {"approach", "in", "enter", "1"}
# Direction aliases recognised as "leaving"
_LEAVE_DIRECTIONS = {"leave", "out", "exit", "2"}


class OccupancyTracker:
    """Thread-safe in-memory occupancy counter with DB persistence and SSE pub/sub."""

    def __init__(self) -> None:
        self._count: int = 0
        self._updated_at: datetime = datetime.now(timezone.utc)
        self._lock: asyncio.Lock = asyncio.Lock()
        self._subscribers: list[asyncio.Queue[dict]] = []

    async def load_from_db(self, db: AsyncSession) -> None:
        """Restore counter from DB on startup.  No-op if no row exists yet."""
        from models.occupancy import OccupancyState
        from sqlalchemy import select

        result = await db.execute(select(OccupancyState).where(OccupancyState.id == 1))
        row = result.scalar_one_or_none()
        if row is not None:
            self._count = row.current_count
            self._updated_at = row.updated_at
            logger.info("OccupancyTracker restored from DB: count={}", self._count)

    async def enter(self, db: AsyncSession) -> None:
        """Increment counter and persist."""
        async with self._lock:
            self._count += 1
            self._updated_at = datetime.now(timezone.utc)
            await self._persist(db)
        await self._notify()

    async def leave(self, db: AsyncSession) -> None:
        """Decrement counter (floor 0) and persist."""
        async with self._lock:
            self._count = max(0, self._count - 1)
            self._updated_at = datetime.now(timezone.utc)
            await self._persist(db)
        await self._notify()

    def snapshot(self) -> dict:
        return {"current": self._count, "updated_at": self._updated_at.isoformat()}

    # ------------------------------------------------------------------
    # SSE pub/sub
    # ------------------------------------------------------------------

    async def subscribe(self) -> asyncio.Queue[dict]:
        q: asyncio.Queue[dict] = asyncio.Queue(maxsize=64)
        self._subscribers.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue[dict]) -> None:
        try:
            self._subscribers.remove(q)
        except ValueError:
            pass

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    async def _notify(self) -> None:
        snap = self.snapshot()
        for q in list(self._subscribers):
            try:
                q.put_nowait(snap)
            except asyncio.QueueFull:
                pass

    async def _persist(self, db: AsyncSession) -> None:
        from models.occupancy import OccupancyState
        from sqlalchemy import select

        result = await db.execute(select(OccupancyState).where(OccupancyState.id == 1))
        row = result.scalar_one_or_none()
        if row is None:
            db.add(OccupancyState(id=1, current_count=self._count, updated_at=self._updated_at))
        else:
            row.current_count = self._count
            row.updated_at = self._updated_at
        await db.commit()


occupancy_tracker = OccupancyTracker()
