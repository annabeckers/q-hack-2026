"""ecosyste.ms API client — fetches top popular packages per registry.

Uses the existing APIClient infrastructure to call:
  GET /registries/{registryName}/packages?sort=dependent_packages_count&order=desc

Maps responses into PopularPackage domain entities.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.domain.slopsquatting.entities import PopularPackage

if TYPE_CHECKING:
    from app.infrastructure.api_client import APIClient

logger = structlog.get_logger(__name__)

# Registries we care about — maps our ecosystem identifiers to ecosyste.ms registry names
DEFAULT_REGISTRIES = {
    "pypi": "pypi.org",
    "npm": "npmjs.org",
    "crates": "crates.io",
    "php": "packagist.org",
    "go": "proxy.golang.org"
}


class EcosystemsClient:
    """Thin wrapper around ecosyste.ms packages API."""

    def __init__(self, api_client: APIClient | None = None) -> None:
        if api_client is None:
            from app.infrastructure.api_client import APIClient as _APIClient

            api_client = _APIClient(
                base_url="https://packages.ecosyste.ms/api/v1",
                auth_type="none",
                headers={"User-Agent": "hackathon-slopsquatting/1.0"},
                cache_ttl=3600,
            )
        self._client = api_client

    async def fetch_top_packages(
        self,
        registry_name: str,
        ecosystem_label: str,
        per_page: int = 100,
        pages: int = 5,
    ) -> list[PopularPackage]:
        """Fetch top packages from a registry sorted by dependent_packages_count.

        Args:
            registry_name: ecosyste.ms registry name (e.g. "pypi.org")
            ecosystem_label: our internal ecosystem label (e.g. "pypi")
            per_page: results per page (max 100)
            pages: number of pages to fetch

        Returns:
            List of PopularPackage domain entities.
        """
        packages: list[PopularPackage] = []

        for page in range(1, pages + 1):
            logger.info(
                "ecosystems_fetch",
                registry=registry_name,
                page=page,
                per_page=per_page,
            )
            try:
                resp = await self._client.get(
                    f"/registries/{registry_name}/packages",
                    params={
                        "sort": "dependent_packages_count",
                        "order": "desc",
                        "per_page": per_page,
                        "page": page,
                    },
                )

                if resp.status_code != 200:
                    logger.warning(
                        "ecosystems_fetch_failed",
                        registry=registry_name,
                        page=page,
                        status=resp.status_code,
                    )
                    break

                data = resp.json()
                if not data:
                    break

                for item in data:
                    packages.append(
                        PopularPackage(
                            name=item.get("name", ""),
                            ecosystem=ecosystem_label,
                            downloads=item.get("downloads") or 0,
                            dependent_packages_count=item.get("dependent_packages_count") or 0,
                            description=(item.get("description") or "")[:500],
                            repository_url=item.get("repository_url"),
                        )
                    )

            except Exception:
                logger.exception(
                    "ecosystems_fetch_error",
                    registry=registry_name,
                    page=page,
                )
                break

        logger.info(
            "ecosystems_fetch_complete",
            registry=registry_name,
            total=len(packages),
        )
        return packages

    async def seed_all(
        self,
        registries: dict[str, str] | None = None,
        per_page: int = 100,
        pages: int = 5,
    ) -> dict[str, list[PopularPackage]]:
        """Fetch top packages for all configured registries.

        Returns:
            Dict mapping ecosystem label → list of PopularPackage.
        """
        if registries is None:
            registries = DEFAULT_REGISTRIES

        results: dict[str, list[PopularPackage]] = {}
        for eco_label, registry_name in registries.items():
            pkgs = await self.fetch_top_packages(
                registry_name=registry_name,
                ecosystem_label=eco_label,
                per_page=per_page,
                pages=pages,
            )
            results[eco_label] = pkgs

        return results
