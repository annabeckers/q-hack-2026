"""Abstract interfaces — domain contracts for infrastructure."""

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from app.domain.analysis import ChatMessageRecord, CompanyReferenceRule, ConversationSummaryRecord, DeterministicMatchRecord
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


class AbstractDeterministicAnalysisRepository(ABC):
    @abstractmethod
    async def ensure_schema(self) -> None: ...

    @abstractmethod
    async def has_completed_analysis(self) -> bool: ...

    @abstractmethod
    async def load_company_reference_rules(self) -> list[CompanyReferenceRule]: ...

    @abstractmethod
    async def load_chat_messages(self) -> list[ChatMessageRecord]: ...

    @abstractmethod
    async def save_analysis_run(self, source_message_count: int, rule_count: int, match_count: int, status: str) -> str: ...

    @abstractmethod
    async def save_company_rules(self, rules: list[CompanyReferenceRule]) -> None: ...

    @abstractmethod
    async def save_matches(self, matches: list[DeterministicMatchRecord]) -> None: ...

    @abstractmethod
    async def save_summaries(self, summaries: list[ConversationSummaryRecord]) -> None: ...

    @abstractmethod
    async def refresh_materialized_views(self) -> None: ...

    # Materialized view query methods
    @abstractmethod
    async def get_overview_stats(self) -> dict[str, Any] | None: ...

    @abstractmethod
    async def get_conversations_from_view(
        self, 
        department: str | None = None,
        provider: str | None = None,
        severity: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def get_top_matches_from_view(
        self,
        department: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]: ...
