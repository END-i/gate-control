from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.relay_job import RelayJob, RelayJobStatus


async def create_relay_job(
    db: AsyncSession,
    event_type: str,
    plate_number: str | None,
    requested_by: str,
    max_attempts: int,
) -> RelayJob:
    item = RelayJob(
        event_type=event_type,
        plate_number=plate_number,
        requested_by=requested_by,
        status=RelayJobStatus.PENDING,
        max_attempts=max_attempts,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


from core.config import get_settings


def _is_postgres() -> bool:
    return get_settings().database_url.startswith("postgresql")


async def claim_next_relay_job(db: AsyncSession) -> RelayJob | None:
    now = datetime.now(timezone.utc)
    stmt = (
        select(RelayJob)
        .where(RelayJob.status == RelayJobStatus.PENDING)
        .where(RelayJob.available_at <= now)
        .order_by(RelayJob.id.asc())
        .limit(1)
    )
    # Prevent two workers from claiming the same job concurrently (PostgreSQL only;
    # SQLite used in tests doesn't support FOR UPDATE SKIP LOCKED).
    if _is_postgres():
        stmt = stmt.with_for_update(skip_locked=True)
    result = await db.execute(stmt)
    item = result.scalar_one_or_none()
    if item is None:
        return None

    item.status = RelayJobStatus.PROCESSING
    await db.commit()
    await db.refresh(item)
    return item


async def mark_relay_job_succeeded(db: AsyncSession, item: RelayJob) -> RelayJob:
    item.status = RelayJobStatus.SUCCEEDED
    item.last_error = None
    await db.commit()
    await db.refresh(item)
    return item


async def mark_relay_job_failed(
    db: AsyncSession,
    item: RelayJob,
    error: str,
    retry_delay_seconds: int,
) -> RelayJob:
    item.attempt_count += 1
    item.last_error = error

    if item.attempt_count >= item.max_attempts:
        item.status = RelayJobStatus.DEAD_LETTER
    else:
        item.status = RelayJobStatus.PENDING
        item.available_at = datetime.now(timezone.utc) + timedelta(seconds=retry_delay_seconds)

    await db.commit()
    await db.refresh(item)
    return item
