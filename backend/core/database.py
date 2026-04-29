from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.config import get_settings
from models.base import Base
from models import admin as _admin_models  # noqa: F401
from models import vehicle as _vehicle_models  # noqa: F401
from models import access_log as _access_log_models  # noqa: F401
from models import security_audit as _security_audit_models  # noqa: F401
from models import webhook_event as _webhook_event_models  # noqa: F401

settings = get_settings()
engine = create_async_engine(settings.database_url, echo=False, future=True)
SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def init_db() -> None:
    app_env = (getattr(settings, "app_env", None) or "development").strip().lower()
    auto_create = (getattr(settings, "auto_create_schema", None) or "").strip()

    if auto_create:
        enabled = auto_create.lower() in {"1", "true", "yes", "on"}
    else:
        # Default policy: create_all only in local/dev/test environments.
        enabled = app_env in {"development", "dev", "local", "test"}

    if not enabled:
        return

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
