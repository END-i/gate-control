from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from models.access_log import AccessLog


async def create_access_log(
    db: AsyncSession,
    license_plate: str,
    access_granted: bool,
    image_path: str | None,
    action_type: str = "auto_entry",
    admin_id: int | None = None,
) -> AccessLog:
    log = AccessLog(
        license_plate=license_plate,
        access_granted=access_granted,
        image_path=image_path,
        action_type=action_type,
        admin_id=admin_id,
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log
