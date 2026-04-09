"""Agent tools with Neo4j and PostgreSQL implementations.

These tools can be used with any agent framework. For framework-specific
decorators, wrap them in the respective skeleton module.
"""

import json
from neo4j import GraphDatabase

from app.config import settings


def get_neo4j_driver():
    return GraphDatabase.driver(
        settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
    )


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
