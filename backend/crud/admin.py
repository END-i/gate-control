from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.admin import Admin


async def get_admin_by_username(db: AsyncSession, username: str) -> Admin | None:
    result = await db.execute(select(Admin).where(Admin.username == username))
    return result.scalar_one_or_none()
