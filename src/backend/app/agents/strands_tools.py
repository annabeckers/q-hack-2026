"""Strands-native tools for the Argus security analysis agent.

These tools use the @tool decorator from Strands SDK, making them
directly usable with any Strands Agent regardless of model provider.
"""

import json

from strands import tool


def _query_postgres(sql: str) -> str:
    """Execute a read-only SQL query against PostgreSQL."""
    if not sql.strip().upper().startswith("SELECT"):
        return json.dumps({"error": "Only SELECT queries are allowed"})

    import psycopg2
    from app.config import settings

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


@tool
def get_findings_summary(finding_type: str = "") -> str:
    """Get a summary of security findings from the analysis pipeline.

    Args:
        finding_type: Optional filter — one of: secret, pii, slopsquatting, sensitivity, complexity, trivial. Leave empty for all.
    """
    where = ""
    if finding_type:
        where = f"WHERE f.analyzer = '{finding_type}'"

    sql = f"""
        SELECT f.analyzer, f.category, f.severity, COUNT(*) as count
        FROM findings f {where}
        GROUP BY f.analyzer, f.category, f.severity
        ORDER BY count DESC
        LIMIT 50
    """
    return _query_postgres(sql)


@tool
def get_department_risk() -> str:
    """Get risk scores aggregated by department. Shows which departments have the most security findings."""
    sql = """
        SELECT
            c.provider,
            COUNT(*) as total_findings,
            COUNT(*) FILTER (WHERE f.severity = 'critical') as critical_count,
            COUNT(*) FILTER (WHERE f.severity = 'high') as high_count,
            COUNT(*) FILTER (WHERE f.severity = 'medium') as medium_count,
            COUNT(*) FILTER (WHERE f.severity = 'low') as low_count
        FROM findings f
        JOIN chats c ON c.id = f.chat_id
        GROUP BY c.provider
        ORDER BY critical_count DESC, high_count DESC
        LIMIT 20
    """
    return _query_postgres(sql)


@tool
def get_recent_secrets(limit: int = 20) -> str:
    """Get the most recent secrets and PII findings detected in AI conversations.

    Args:
        limit: Number of recent findings to return. Default 20.
    """
    sql = f"""
        SELECT f.analyzer, f.severity, f.snippet, f.title, f.created_at
        FROM findings f
        WHERE f.analyzer IN ('secrets', 'pii')
        ORDER BY f.created_at DESC
        LIMIT {min(limit, 100)}
    """
    return _query_postgres(sql)


@tool
def get_chat_stats() -> str:
    """Get overall statistics about imported AI chat conversations — total count, models used, providers."""
    sql = """
        SELECT
            COUNT(*) as total_messages,
            COUNT(DISTINCT conversation_key) as total_conversations,
            COUNT(DISTINCT provider) as provider_count,
            COUNT(DISTINCT model_name) as model_count,
            MIN(conversation_timestamp) as earliest,
            MAX(conversation_timestamp) as latest
        FROM chats
    """
    return _query_postgres(sql)


@tool
def get_dashboard_overview() -> str:
    """Get the full dashboard overview — total messages, conversations, findings by severity. This is the main summary endpoint."""
    sql = """
        SELECT *
        FROM mv_dashboard_overview
        LIMIT 1
    """
    return _query_postgres(sql)


# All tools as a list for easy import
ANALYSIS_TOOLS = [
    get_findings_summary,
    get_department_risk,
    get_recent_secrets,
    get_chat_stats,
    get_dashboard_overview,
]
