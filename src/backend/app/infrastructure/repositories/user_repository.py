"""User repository — works directly with domain entities via imperative mapping.

No ORM model conversion needed. SQLAlchemy operates on User dataclass directly.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import User
from app.domain.interfaces import AbstractUserRepository


class UserRepository(AbstractUserRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, id: UUID) -> User | None:
        result = await self._session.execute(select(User).where(User.id == id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def save(self, entity: User) -> User:
        merged = await self._session.merge(entity)
        await self._session.flush()
        return merged

    async def delete(self, id: UUID) -> None:
        result = await self._session.execute(select(User).where(User.id == id))
        entity = result.scalar_one_or_none()
        if entity:
            await self._session.delete(entity)
            await self._session.flush()

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[User]:
        result = await self._session.execute(select(User).limit(limit).offset(offset))
        return list(result.scalars().all())
