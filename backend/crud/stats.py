from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.access_log import AccessLog
from models.vehicle import Vehicle


async def get_stats(db: AsyncSession) -> dict[str, int]:
    now = datetime.now(timezone.utc)
    day_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
    day_end = day_start + timedelta(days=1)

    total_vehicles = (await db.execute(select(func.count(Vehicle.id)))).scalar_one()

    today_access_total = (
        await db.execute(
            select(func.count(AccessLog.id)).where(
                AccessLog.timestamp >= day_start,
                AccessLog.timestamp < day_end,
            )
        )
    ).scalar_one()

    today_denied_total = (
        await db.execute(
            select(func.count(AccessLog.id)).where(
                AccessLog.timestamp >= day_start,
                AccessLog.timestamp < day_end,
                AccessLog.access_granted.is_(False),
            )
        )
    ).scalar_one()

    return {
        "total_vehicles": total_vehicles,
        "today_access_total": today_access_total,
        "today_denied_total": today_denied_total,
    }
