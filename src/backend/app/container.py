"""Composition root — wires all dependencies."""

from redis.asyncio import Redis
from neo4j import AsyncGraphDatabase

try:
    import chromadb
except Exception:  # pragma: no cover - optional test/runtime dependency
    chromadb = None

from app.config import settings
from app.infrastructure.database import async_engine, async_session_factory


class Container:
    """DI container that initializes and holds all infrastructure clients."""

    def __init__(self):
        self.db_engine = async_engine
        self.db_session_factory = async_session_factory
        self.redis: Redis | None = None
        self.neo4j_driver = None
        self.chroma_client: chromadb.HttpClient | None = None

    async def init(self):
        """Initialize all external connections."""
        self.redis = Redis.from_url(settings.redis_url, decode_responses=True)
        self.neo4j_driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
        if chromadb is not None:
            self.chroma_client = chromadb.HttpClient(
                host=settings.chroma_host,
                port=settings.chroma_port,
            )
        else:
            self.chroma_client = None

    async def close(self):
        """Cleanup all connections."""
        if self.redis:
            await self.redis.close()
        if self.neo4j_driver:
            await self.neo4j_driver.close()
        await self.db_engine.dispose()
