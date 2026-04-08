from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.infrastructure.mapping import start_mappers

# Start imperative mappers on import — maps domain entities to SQL tables
start_mappers()

async_engine = create_async_engine(settings.database_url, echo=settings.debug)
async_session_factory = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
