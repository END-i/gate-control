from sqlalchemy import select

from core.config import get_settings
from core.database import SessionLocal
from core.security import hash_password
from models.admin import Admin


async def seed_initial_admin() -> None:
    settings = get_settings()

    if not settings.admin_username or not settings.admin_password:
        raise RuntimeError("ADMIN_USERNAME and ADMIN_PASSWORD must be set")

    async with SessionLocal() as db:
        existing = await db.execute(select(Admin.id).limit(1))
        first_admin_id = existing.scalar_one_or_none()

        if first_admin_id is not None:
            return

        admin = Admin(
            username=settings.admin_username,
            hashed_password=hash_password(settings.admin_password),
        )
        db.add(admin)
        await db.commit()
