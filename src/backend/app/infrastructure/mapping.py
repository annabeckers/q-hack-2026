"""Imperative mapping — maps domain entities to SQL tables without polluting them.

This is the DDD-proper approach: domain entities stay as pure dataclasses,
and this module tells SQLAlchemy how to persist them. No ORM base classes,
no mapped_column decorators on entities.

The entities ARE the mapped objects — no conversion needed in repositories.

Usage:
    from app.infrastructure.mapping import metadata, start_mappers
    start_mappers()  # Call once at app startup
"""

from sqlalchemy import Boolean, Column, DateTime, String, Table, Text, Uuid
from sqlalchemy.orm import registry

from app.domain.entities import User, Document, DataSource

mapper_registry = registry()
metadata = mapper_registry.metadata

# ── Tables ────────────────────────────────────────────────────────────────────

users_table = Table(
    "users",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("email", String(255), unique=True, nullable=False, index=True),
    Column("hashed_password", String(255), nullable=False),
    Column("name", String(255), nullable=False),
    Column("is_active", Boolean, default=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)

documents_table = Table(
    "documents",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("title", String(500), nullable=False),
    Column("source", String(1000), nullable=False),
    Column("source_type", String(50), nullable=False),
    Column("content_preview", Text, nullable=True),
    Column("metadata_json", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)

data_sources_table = Table(
    "data_sources",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("name", String(255), nullable=False, unique=True),
    Column("source_type", String(50), nullable=False),
    Column("connection_string", String(1000), nullable=True),
    Column("config_json", Text, nullable=True),
    Column("is_active", Boolean, default=True),
    Column("last_sync_at", DateTime(timezone=True), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)


# ── Imperative Mapping ───────────────────────────────────────────────────────

_mappers_started = False


def start_mappers() -> None:
    """Map domain entities to SQL tables. Call once at app startup.

    After this call, SQLAlchemy knows how to persist User, Document, etc.
    directly — no separate ORM model classes needed.
    """
    global _mappers_started
    if _mappers_started:
        return

    mapper_registry.map_imperatively(User, users_table)
    mapper_registry.map_imperatively(Document, documents_table)
    mapper_registry.map_imperatively(DataSource, data_sources_table)

    _mappers_started = True
