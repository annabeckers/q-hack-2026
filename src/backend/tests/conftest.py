"""Shared test fixtures — SQLite in-memory database, async client, test user."""

from collections.abc import AsyncGenerator
import os
from pathlib import Path
import sys

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite://")

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.auth.password import hash_password
from app.domain.entities import User
from app.infrastructure.mapping import metadata, start_mappers

# ---------------------------------------------------------------------------
# Engine + session factory for tests (SQLite in-memory, async via aiosqlite)
# ---------------------------------------------------------------------------
test_engine = create_async_engine("sqlite+aiosqlite://", echo=False)
test_session_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


# ---------------------------------------------------------------------------
# Ensure imperative mappers are registered before any table creation
# ---------------------------------------------------------------------------
start_mappers()


@pytest.fixture(autouse=True)
async def _setup_database():
    """Create all tables before each test, drop them after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(metadata.drop_all)


@pytest.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a clean async session scoped to a single test."""
    async with test_session_factory() as sess:
        yield sess


class _MinimalContainer:
    """Stub container so health endpoint doesn't crash without lifespan."""

    def __init__(self, session_factory):
        self._session_factory = session_factory
        self.redis = None
        self.neo4j_driver = None

    def db_session_factory(self):
        return self._session_factory()


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client wired to the FastAPI app with test DB override."""
    import app.infrastructure.database as db_module

    # Monkey-patch the session factory so endpoints use the test database
    original_factory = db_module.async_session_factory
    db_module.async_session_factory = test_session_factory

    from app.main import app

    # Attach a minimal container so health endpoint works without lifespan
    app.state.container = _MinimalContainer(test_session_factory)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Restore original factory
    db_module.async_session_factory = original_factory


@pytest.fixture
async def test_user(session: AsyncSession) -> User:
    """Insert and return a test user with known credentials."""
    user = User(
        email="test@example.com",
        hashed_password=hash_password("testpassword123"),
        name="Test User",
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
