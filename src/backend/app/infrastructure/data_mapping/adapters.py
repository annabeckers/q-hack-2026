"""Source adapters — normalize different data sources into a common format."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class DataRecord:
    """Normalized data record from any source."""
    source: str
    source_type: str
    raw: dict[str, Any]
    normalized: dict[str, Any] | None = None


class SourceAdapter(ABC):
    """Base adapter for data sources. Implement for each external data format."""

    @abstractmethod
    async def fetch(self, **kwargs) -> list[DataRecord]:
        """Fetch records from the source."""
        ...

    @abstractmethod
    def normalize(self, record: DataRecord) -> DataRecord:
        """Normalize a raw record into a standard schema."""
        ...


class APIAdapter(SourceAdapter):
    """Adapter for REST API data sources."""

    def __init__(self, base_url: str, headers: dict | None = None):
        self.base_url = base_url
        self.headers = headers or {}

    async def fetch(self, endpoint: str = "", params: dict | None = None) -> list[DataRecord]:
        import httpx

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                params=params or {},
            )
            resp.raise_for_status()
            data = resp.json()

        items = data if isinstance(data, list) else [data]
        return [
            DataRecord(source=self.base_url, source_type="api", raw=item)
            for item in items
        ]

    def normalize(self, record: DataRecord) -> DataRecord:
        # Override per API — default is passthrough
        record.normalized = record.raw
        return record


class DatabaseAdapter(SourceAdapter):
    """Adapter for database query results."""

    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def fetch(self, query: str = "", params: dict | None = None) -> list[DataRecord]:
        async with self.session_factory() as session:
            result = await session.execute(query, params or {})
            rows = result.mappings().all()
            return [
                DataRecord(source="postgres", source_type="database", raw=dict(row))
                for row in rows
            ]

    def normalize(self, record: DataRecord) -> DataRecord:
        record.normalized = record.raw
        return record
