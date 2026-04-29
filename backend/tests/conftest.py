import os
from pathlib import Path

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

os.environ.setdefault('DATABASE_URL', 'sqlite+aiosqlite:///./test.db')
os.environ.setdefault('SECRET_KEY', 'test-secret-key-0123456789abcdef')
os.environ.setdefault('RELAY_IP', 'http://relay.local/trigger')
os.environ.setdefault('RELAY_USERNAME', 'relay-user')
os.environ.setdefault('RELAY_PASSWORD', 'relay-pass')
os.environ.setdefault('FRONTEND_URL', 'http://localhost:3000')
os.environ.setdefault('WEBHOOK_SHARED_SECRET', 'webhook-secret')
os.environ.setdefault('WEBHOOK_AUTH_MODE', 'token')
os.environ.setdefault('WEBHOOK_HMAC_SECRET', 'hmac-secret')
os.environ.setdefault('WEBHOOK_MAX_SKEW_SECONDS', '300')
os.environ.setdefault('ADMIN_USERNAME', 'admin')
os.environ.setdefault('ADMIN_PASSWORD', 'admin')
os.environ.setdefault('ANPR_SKIP_STARTUP_TASKS', '1')

from core.config import get_settings  # noqa: E402
from core.database import get_db  # noqa: E402
from core.security import hash_password  # noqa: E402
from main import app  # noqa: E402
from models import Admin, Base  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_settings_cache() -> None:
    get_settings.cache_clear()


@pytest_asyncio.fixture()
async def db_session(tmp_path: Path) -> AsyncSession:
    db_file = tmp_path / 'test.sqlite'
    engine = create_async_engine(f'sqlite+aiosqlite:///{db_file}', future=True)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        admin = Admin(username='admin', hashed_password=hash_password('admin'))
        session.add(admin)
        await session.commit()
        yield session

    await engine.dispose()


@pytest.fixture()
def client(db_session: AsyncSession) -> TestClient:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
