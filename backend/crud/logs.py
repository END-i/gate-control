from __future__ import annotations

from datetime import datetime

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.access_log import AccessLog


async def list_access_logs(
    db: AsyncSession,
    limit: int,
    offset: int,
    plate: str | None,
    date_from: datetime | None,
    date_to: datetime | None,
) -> tuple[list[AccessLog], int]:
    filters = []

    if plate:
        filters.append(AccessLog.license_plate.ilike(f"%{plate}%"))
    if date_from:
        filters.append(AccessLog.timestamp >= date_from)
    if date_to:
        filters.append(AccessLog.timestamp <= date_to)

    base_query = select(AccessLog)
    count_query = select(func.count(AccessLog.id))

    if filters:
        condition = and_(*filters)
        base_query = base_query.where(condition)
        count_query = count_query.where(condition)

    total = (await db.execute(count_query)).scalar_one()
    result = await db.execute(
        base_query.order_by(AccessLog.timestamp.desc()).limit(limit).offset(offset)
    )

    return list(result.scalars().all()), total


async def list_access_logs_after_id(
    db: AsyncSession,
    after_id: int,
    limit: int = 100,
) -> list[AccessLog]:
    result = await db.execute(
        select(AccessLog)
        .where(AccessLog.id > after_id)
        .order_by(AccessLog.id.asc())
        .limit(limit)
    )
    return list(result.scalars().all())
