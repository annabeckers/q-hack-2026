"""Neo4j graph builder — create entity relationships from normalized data."""

from neo4j import AsyncGraphDatabase

from app.config import settings
from app.infrastructure.data_mapping.adapters import DataRecord


class GraphBuilder:
    """Build a Neo4j graph from normalized data records.

    Usage:
        builder = GraphBuilder()
        await builder.connect()
        await builder.add_records(records, entity_type="Document", id_field="id")
        await builder.add_relationship(
            from_records=docs, to_records=authors,
            from_id="doc_id", to_id="author_id",
            rel_type="AUTHORED_BY",
        )
        await builder.close()
    """

    def __init__(self):
        self.driver = None

    async def connect(self):
        self.driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
        )

    async def close(self):
        if self.driver:
            await self.driver.close()

    async def add_records(
        self, records: list[DataRecord], entity_type: str, id_field: str
    ) -> int:
        """Create nodes from data records."""
        count = 0
        async with self.driver.session() as session:
            for record in records:
                data = record.normalized or record.raw
                entity_id = data.get(id_field, str(count))

                # Build property string dynamically
                props = {k: v for k, v in data.items() if isinstance(v, (str, int, float, bool))}
                props["_source"] = record.source
                props["_source_type"] = record.source_type

                await session.run(
                    f"MERGE (n:{entity_type} {{id: $id}}) SET n += $props",
                    id=str(entity_id),
                    props=props,
                )
                count += 1
        return count

    async def add_relationship(
        self,
        from_type: str,
        to_type: str,
        from_id: str,
        to_id: str,
        rel_type: str,
        properties: dict | None = None,
    ) -> None:
        """Create a relationship between two entity types."""
        async with self.driver.session() as session:
            query = (
                f"MATCH (a:{from_type} {{id: $from_id}}) "
                f"MATCH (b:{to_type} {{id: $to_id}}) "
                f"MERGE (a)-[r:{rel_type}]->(b)"
            )
            if properties:
                query += " SET r += $props"

            await session.run(
                query, from_id=from_id, to_id=to_id, props=properties or {}
            )
