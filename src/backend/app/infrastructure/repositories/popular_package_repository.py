"""SQLAlchemy async repository for popular packages."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.slopsquatting.entities import PopularPackage
from app.domain.slopsquatting.interfaces import AbstractPopularPackageRepository


class PopularPackageRepository(AbstractPopularPackageRepository):
    """Postgres-backed repository for popular packages."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_all_names(self) -> list[PopularPackage]:
        sql = text("SELECT id, name, ecosystem, downloads, dependent_packages_count, description, repository_url, created_at, updated_at FROM popular_packages")
        async with self._session_factory() as session:
            result = await session.execute(sql)
            return [
                PopularPackage(
                    id=row.id,
                    name=row.name,
                    ecosystem=row.ecosystem,
                    downloads=row.downloads,
                    dependent_packages_count=row.dependent_packages_count,
                    description=row.description,
                    repository_url=row.repository_url,
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                )
                for row in result
            ]

    async def get_by_ecosystem(self, ecosystem: str) -> list[PopularPackage]:
        sql = text(
            "SELECT id, name, ecosystem, downloads, dependent_packages_count, description, repository_url, created_at, updated_at "
            "FROM popular_packages WHERE ecosystem = :ecosystem ORDER BY dependent_packages_count DESC"
        )
        async with self._session_factory() as session:
            result = await session.execute(sql, {"ecosystem": ecosystem})
            return [
                PopularPackage(
                    id=row.id,
                    name=row.name,
                    ecosystem=row.ecosystem,
                    downloads=row.downloads,
                    dependent_packages_count=row.dependent_packages_count,
                    description=row.description,
                    repository_url=row.repository_url,
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                )
                for row in result
            ]

    async def find_by_name(self, name: str) -> list[PopularPackage]:
        sql = text(
            "SELECT id, name, ecosystem, downloads, dependent_packages_count, description, repository_url, created_at, updated_at "
            "FROM popular_packages WHERE LOWER(name) = LOWER(:name)"
        )
        async with self._session_factory() as session:
            result = await session.execute(sql, {"name": name})
            return [
                PopularPackage(
                    id=row.id,
                    name=row.name,
                    ecosystem=row.ecosystem,
                    downloads=row.downloads,
                    dependent_packages_count=row.dependent_packages_count,
                    description=row.description,
                    repository_url=row.repository_url,
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                )
                for row in result
            ]

    async def save_batch(self, packages: list[PopularPackage]) -> int:
        if not packages:
            return 0

        upsert_sql = text("""
            INSERT INTO popular_packages (name, ecosystem, downloads, dependent_packages_count, description, repository_url)
            VALUES (:name, :ecosystem, :downloads, :dependent_packages_count, :description, :repository_url)
            ON CONFLICT (ecosystem, name)
            DO UPDATE SET
                downloads = EXCLUDED.downloads,
                dependent_packages_count = EXCLUDED.dependent_packages_count,
                description = EXCLUDED.description,
                repository_url = EXCLUDED.repository_url,
                updated_at = NOW()
        """)

        async with self._session_factory() as session:
            async with session.begin():
                for pkg in packages:
                    await session.execute(
                        upsert_sql,
                        {
                            "name": pkg.name,
                            "ecosystem": pkg.ecosystem,
                            "downloads": pkg.downloads,
                            "dependent_packages_count": pkg.dependent_packages_count,
                            "description": pkg.description,
                            "repository_url": pkg.repository_url,
                        },
                    )
        return len(packages)

    async def count_by_ecosystem(self) -> dict[str, int]:
        sql = text("SELECT ecosystem, COUNT(*) as cnt FROM popular_packages GROUP BY ecosystem ORDER BY cnt DESC")
        async with self._session_factory() as session:
            result = await session.execute(sql)
            return {row.ecosystem: row.cnt for row in result}
