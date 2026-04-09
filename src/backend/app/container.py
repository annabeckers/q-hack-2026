"""Composition root — wires all dependencies."""

import structlog

from app.config import settings
from app.infrastructure.database import async_engine, async_session_factory

log = structlog.get_logger()


class Container:
    """DI container that initializes and holds all infrastructure clients."""

    def __init__(self):
        self.db_engine = async_engine
        self.db_session_factory = async_session_factory

    async def init(self):
        """Initialize all external connections."""
        log.info("container_initialized", database=True)

    async def close(self):
        """Cleanup all connections."""
        await self.db_engine.dispose()
