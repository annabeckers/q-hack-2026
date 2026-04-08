"""Abstract interfaces — domain contracts for infrastructure."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities import User, Document, DataSource
from app.domain.dashboard import ConversationRecord, FindingRecord, UsageRecord


class AbstractRepository[T](ABC):
    @abstractmethod
    async def get_by_id(self, id: UUID) -> T | None: ...

    @abstractmethod
    async def save(self, entity: T) -> T: ...

    @abstractmethod
    async def delete(self, id: UUID) -> None: ...

    @abstractmethod
    async def list_all(self, limit: int = 100, offset: int = 0) -> list[T]: ...


class AbstractUserRepository(AbstractRepository[User]):
    @abstractmethod
    async def get_by_email(self, email: str) -> User | None: ...


class AbstractDocumentRepository(AbstractRepository[Document]):
    @abstractmethod
    async def get_by_source(self, source: str) -> Document | None: ...

    @abstractmethod
    async def search_by_title(self, query: str) -> list[Document]: ...


class AbstractDataSourceRepository(AbstractRepository[DataSource]):
    @abstractmethod
    async def get_by_name(self, name: str) -> DataSource | None: ...

    @abstractmethod
    async def get_active(self) -> list[DataSource]: ...


class AbstractDashboardRepository(ABC):
    @abstractmethod
    def list_usage_records(self) -> list[UsageRecord]: ...

    @abstractmethod
    def list_conversations(self) -> list[ConversationRecord]: ...

    @abstractmethod
    def list_findings(self) -> list[FindingRecord]: ...

    @abstractmethod
    def update_finding_status(self, finding_id: str, status: str, notes: str | None = None) -> FindingRecord | None: ...
