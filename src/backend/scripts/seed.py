"""Database seed script — populate with demo data for quick demos.

Usage: uv run python scripts/seed.py
"""

import asyncio
from uuid import uuid4
from datetime import datetime, timezone

from app.infrastructure.database import async_session_factory
from app.infrastructure.mapping import start_mappers
from app.domain.entities import User, Document, DataSource
from app.auth.password import hash_password


async def seed():
    start_mappers()

    async with async_session_factory() as session:
        async with session.begin():
            # Demo users
            users = [
                User(
                    id=uuid4(),
                    email="admin@hackathon.dev",
                    hashed_password=hash_password("admin123"),
                    name="Admin",
                    is_active=True,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                ),
                User(
                    id=uuid4(),
                    email="demo@hackathon.dev",
                    hashed_password=hash_password("demo123"),
                    name="Demo User",
                    is_active=True,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                ),
            ]

            # Demo documents
            documents = [
                Document(
                    id=uuid4(),
                    title="Sample Report Q1 2026",
                    source="resources/data/sample-report.pdf",
                    source_type="pdf",
                    content_preview="Quarterly performance analysis showing 15% growth...",
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                ),
                Document(
                    id=uuid4(),
                    title="Customer Dataset",
                    source="resources/data/customers.csv",
                    source_type="csv",
                    content_preview="1000 customer records with demographics and purchase history",
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                ),
            ]

            # Demo data sources
            data_sources = [
                DataSource(
                    id=uuid4(),
                    name="internal-api",
                    source_type="api",
                    connection_string="https://api.example.com/v1",
                    is_active=True,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                ),
            ]

            for entity in users + documents + data_sources:
                session.add(entity)

    print(f"Seeded: {len(users)} users, {len(documents)} documents, {len(data_sources)} data sources")
    print("Login: admin@hackathon.dev / admin123")


if __name__ == "__main__":
    asyncio.run(seed())
