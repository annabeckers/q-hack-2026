"""Domain entities — pure Python, no framework imports.

These dataclasses are mapped to SQL tables via imperative mapping
in app/infrastructure/mapping.py. They never import SQLAlchemy.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass
class BaseEntity:
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class User(BaseEntity):
    email: str = ""
    hashed_password: str = ""
    name: str = ""
    is_active: bool = True


@dataclass
class Document(BaseEntity):
    """A document ingested from any source."""
    title: str = ""
    source: str = ""
    source_type: str = ""  # "pdf", "csv", "json", "api"
    content_preview: str | None = None
    metadata_json: str | None = None


@dataclass
class DataSource(BaseEntity):
    """A registered external data source."""
    name: str = ""
    source_type: str = ""  # "postgres", "api", "file", "s3"
    connection_string: str | None = None
    config_json: str | None = None
    is_active: bool = True
    last_sync_at: datetime | None = None
