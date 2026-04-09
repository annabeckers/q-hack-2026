"""Domain entities for slopsquatting detection — pure Python, no framework imports.

PopularPackage represents a well-known package from a registry ecosystem.
Mapped to the popular_packages SQL table via imperative mapping.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class PopularPackage:
    """A known-legitimate popular package from a package registry."""

    id: int | None = None
    name: str = ""
    ecosystem: str = ""  # "pypi", "npmjs.org", "crates.io", etc.
    downloads: int = 0
    dependent_packages_count: int = 0
    description: str | None = None
    repository_url: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
