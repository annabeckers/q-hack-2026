"""Abstract interfaces — domain contracts for slopsquatting infrastructure."""

from abc import ABC, abstractmethod

from app.domain.slopsquatting.entities import PopularPackage


class AbstractPopularPackageRepository(ABC):
    """Repository interface for popular packages."""

    @abstractmethod
    async def get_all_names(self) -> list[PopularPackage]:
        """Return all popular packages (name + ecosystem)."""
        ...

    @abstractmethod
    async def get_by_ecosystem(self, ecosystem: str) -> list[PopularPackage]:
        """Return popular packages filtered by ecosystem."""
        ...

    @abstractmethod
    async def find_by_name(self, name: str) -> list[PopularPackage]:
        """Find exact matches by package name across all ecosystems."""
        ...

    @abstractmethod
    async def save_batch(self, packages: list[PopularPackage]) -> int:
        """Upsert a batch of popular packages. Returns count of rows affected."""
        ...

    @abstractmethod
    async def count_by_ecosystem(self) -> dict[str, int]:
        """Return counts of packages per ecosystem."""
        ...
