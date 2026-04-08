"""Unit of Work — atomic transactions across multiple repositories.

Ensures all-or-nothing persistence. If any repo operation fails,
everything rolls back.

Usage:
    async with UnitOfWork(session_factory) as uow:
        user = User(email="x@y.com", ...)
        await uow.users.save(user)
        doc = Document(title="Report", ...)
        await uow.documents.save(doc)
        await uow.commit()
        # If commit fails, both are rolled back
"""

from app.infrastructure.database import async_session_factory
from app.infrastructure.repositories.user_repository import UserRepository


class UnitOfWork:
    """Manages a transactional scope across multiple repositories."""

    def __init__(self, session_factory=None):
        self._session_factory = session_factory or async_session_factory

    async def __aenter__(self):
        self._session = self._session_factory()
        self._transaction = await self._session.begin()
        self.users = UserRepository(self._session)
        # Add more repos as needed:
        # self.documents = DocumentRepository(self._session)
        # self.data_sources = DataSourceRepository(self._session)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.rollback()
        await self._session.close()

    async def commit(self):
        await self._session.commit()

    async def rollback(self):
        await self._session.rollback()
