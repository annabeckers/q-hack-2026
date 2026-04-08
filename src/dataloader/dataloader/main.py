"""Dataloader CLI — extract, analyze, and ingest documents."""

import asyncio
import sys
from pathlib import Path

import structlog

from dataloader.extractors import get_extractor
from dataloader.ingest import ChromaIngestor, Neo4jIngestor
from dataloader.gemini import analyze_document, extract_entities

log = structlog.get_logger()


async def extract_command(file_path: str) -> None:
    """Extract text from a document and print it."""
    path = Path(file_path)
    extractor = get_extractor(path)
    docs = await extractor.extract(path)
    for doc in docs:
        print(f"--- {doc.source} ---")
        print(doc.content[:500])
        print()


async def ingest_command(file_path: str, collection: str = "documents") -> None:
    """Extract, analyze with Gemini, and ingest into ChromaDB + Neo4j."""
    path = Path(file_path)

    # Extract
    extractor = get_extractor(path)
    docs = await extractor.extract(path)
    log.info("extracted", file=str(path), doc_count=len(docs))

    # Ingest into ChromaDB
    chroma = ChromaIngestor(collection)
    count = chroma.ingest(docs)
    log.info("chroma_ingested", count=count)

    # Analyze with Gemini and build graph (if API key is set)
    from dataloader.config import settings

    if settings.google_api_key:
        neo4j = Neo4jIngestor()
        for doc in docs:
            entities = await extract_entities(doc.content)
            graph_count = neo4j.ingest_entities(doc.source, entities)
            log.info("neo4j_ingested", source=doc.source, entities=graph_count)
        neo4j.close()
    else:
        log.warning("skipping_gemini", reason="GOOGLE_API_KEY not set")


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m dataloader.main <extract|ingest> <file_path> [collection]")
        sys.exit(1)

    command = sys.argv[1]
    file_path = sys.argv[2] if len(sys.argv) > 2 else ""

    if command == "extract":
        asyncio.run(extract_command(file_path))
    elif command == "ingest":
        collection = sys.argv[3] if len(sys.argv) > 3 else "documents"
        asyncio.run(ingest_command(file_path, collection))
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
