"""Agent tools with real ChromaDB + Neo4j implementations.

These tools can be used with any agent framework. For framework-specific
decorators, wrap them in the respective skeleton module.
"""

import json
import chromadb
from neo4j import GraphDatabase

from app.config import settings


def get_chroma_client() -> chromadb.HttpClient:
    return chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)


def get_neo4j_driver():
    return GraphDatabase.driver(
        settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
    )


def search_knowledge_base(query: str, collection: str = "documents", n_results: int = 5) -> str:
    """Search the ChromaDB knowledge base for relevant information.

    Args:
        query: The search query string.
        collection: ChromaDB collection name.
        n_results: Number of results to return.

    Returns:
        JSON string of matching documents.
    """
    client = get_chroma_client()
    coll = client.get_or_create_collection(collection)
    results = coll.query(query_texts=[query], n_results=n_results)

    docs = []
    for i, doc in enumerate(results["documents"][0]):
        meta = results["metadatas"][0][i] if results["metadatas"] else {}
        docs.append({"content": doc[:500], "metadata": meta})

    return json.dumps(docs, indent=2)


def query_graph(cypher: str) -> str:
    """Execute a Cypher query against the Neo4j graph database.

    Args:
        cypher: The Cypher query to execute.

    Returns:
        JSON string of query results.
    """
    driver = get_neo4j_driver()
    with driver.session() as session:
        result = session.run(cypher)
        records = [dict(record) for record in result]
    driver.close()

    # Serialize Neo4j types to JSON-safe format
    def serialize(obj):
        if hasattr(obj, "__dict__"):
            return str(obj)
        return obj

    return json.dumps(records, default=serialize, indent=2)


def search_postgres(sql: str) -> str:
    """Execute a read-only SQL query against PostgreSQL.

    Args:
        sql: SELECT query to execute.

    Returns:
        JSON string of query results.

    Note: Only SELECT queries are allowed for safety.
    """
    if not sql.strip().upper().startswith("SELECT"):
        return json.dumps({"error": "Only SELECT queries are allowed"})

    # Use synchronous connection for tool simplicity
    import psycopg2

    # Parse the async URL to sync format
    sync_url = settings.database_url.replace("+asyncpg", "")
    conn = psycopg2.connect(sync_url)
    try:
        cur = conn.cursor()
        cur.execute(sql)
        columns = [desc[0] for desc in cur.description] if cur.description else []
        rows = [dict(zip(columns, row)) for row in cur.fetchall()]
        return json.dumps(rows, default=str, indent=2)
    finally:
        conn.close()
