"""Ingestion pipelines — load extracted documents into vector/graph stores."""

import chromadb

from dataloader.config import settings
from dataloader.extractors import ExtractedDocument


class ChromaIngestor:
    """Ingest documents into ChromaDB for vector search."""

    def __init__(self, collection_name: str = "documents"):
        self.client = chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)
        self.collection = self.client.get_or_create_collection(collection_name)

    def ingest(self, documents: list[ExtractedDocument]) -> int:
        if not documents:
            return 0

        self.collection.add(
            ids=[doc.source for doc in documents],
            documents=[doc.content for doc in documents],
            metadatas=[doc.metadata for doc in documents],
        )
        return len(documents)

    def query(self, query: str, n_results: int = 5) -> list[dict]:
        results = self.collection.query(query_texts=[query], n_results=n_results)
        return [
            {"source": id_, "content": doc, "metadata": meta}
            for id_, doc, meta in zip(
                results["ids"][0], results["documents"][0], results["metadatas"][0]
            )
        ]


class Neo4jIngestor:
    """Ingest entity relationships into Neo4j graph database."""

    def __init__(self):
        from neo4j import GraphDatabase

        self.driver = GraphDatabase.driver(
            settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
        )

    def ingest_entities(self, source: str, entities: dict) -> int:
        """Ingest extracted entities as graph nodes with relationships to source."""
        count = 0
        with self.driver.session() as session:
            # Create source node
            session.run(
                "MERGE (s:Source {name: $name})",
                name=source,
            )

            for entity_type, values in entities.items():
                if not isinstance(values, list):
                    continue
                for value in values:
                    session.run(
                        f"MERGE (e:{entity_type.title()} {{name: $name}}) "
                        "MERGE (s:Source {name: $source}) "
                        "MERGE (s)-[:CONTAINS]->(e)",
                        name=str(value),
                        source=source,
                    )
                    count += 1
        return count

    def close(self):
        self.driver.close()
