"""Built-in tools — registered with the global tool registry.

These are the default tools available to all agent frameworks.
Import this module to register them: `import app.agents.tools_builtin`
"""

from app.agents.tool_registry import tool_registry
from app.agents.tools import search_knowledge_base, query_graph, search_postgres


# Register existing tools
tool_registry.register(tags=["database", "search"])(search_knowledge_base)
tool_registry.register(tags=["database", "graph"])(query_graph)
tool_registry.register(tags=["database", "sql"])(search_postgres)


@tool_registry.register(tags=["utility"])
async def fetch_url(url: str) -> str:
    """Fetch content from a URL and return the text.

    Args:
        url: The URL to fetch.
    """
    import httpx

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url, follow_redirects=True)
        resp.raise_for_status()
        content_type = resp.headers.get("content-type", "")
        if "json" in content_type:
            import json
            return json.dumps(resp.json(), indent=2)
        return resp.text[:5000]


@tool_registry.register(tags=["utility", "data"])
def compare_datasets(dataset_a: str, dataset_b: str) -> str:
    """Compare two JSON datasets and return differences.

    Args:
        dataset_a: First dataset as JSON string.
        dataset_b: Second dataset as JSON string.
    """
    import json

    a = json.loads(dataset_a)
    b = json.loads(dataset_b)

    if isinstance(a, list) and isinstance(b, list):
        return json.dumps({
            "a_count": len(a),
            "b_count": len(b),
            "a_only_count": len(a) - len(b) if len(a) > len(b) else 0,
            "b_only_count": len(b) - len(a) if len(b) > len(a) else 0,
            "sample_a": a[0] if a else None,
            "sample_b": b[0] if b else None,
        }, indent=2)

    if isinstance(a, dict) and isinstance(b, dict):
        a_keys = set(a.keys())
        b_keys = set(b.keys())
        return json.dumps({
            "a_only_keys": list(a_keys - b_keys),
            "b_only_keys": list(b_keys - a_keys),
            "shared_keys": list(a_keys & b_keys),
            "different_values": {
                k: {"a": a[k], "b": b[k]}
                for k in a_keys & b_keys if a[k] != b[k]
            },
        }, indent=2)

    return json.dumps({"error": "Both datasets must be arrays or objects"})


@tool_registry.register(tags=["utility", "rust"])
async def rust_process(data: str, operation: str) -> str:
    """Send data to the Rust worker for high-performance processing.

    Args:
        data: JSON array of arrays (rows of strings).
        operation: One of: deduplicate, aggregate, similarity, transform.
    """
    import httpx
    import json
    from app.config import settings

    payload = json.loads(data) if isinstance(data, str) else data
    async with httpx.AsyncClient(timeout=30) as client:
        if operation == "similarity":
            resp = await client.post(f"{settings.rust_worker_url}/similarity", json=payload)
        elif operation == "transform":
            resp = await client.post(f"{settings.rust_worker_url}/transform", json=payload)
        else:
            resp = await client.post(f"{settings.rust_worker_url}/process", json={
                "data": payload, "operation": operation,
            })
        return json.dumps(resp.json(), indent=2)


# ── Hackathon-specific analysis tools ─────────────────────────────────────


@tool_registry.register(tags=["analysis", "dashboard"])
def get_findings_summary(finding_type: str = "") -> str:
    """Get a summary of security findings from the analysis pipeline.

    Args:
        finding_type: Optional filter — one of: secret, pii, slopsquatting, sensitivity, complexity, trivial. Leave empty for all.
    """
    import json
    from app.agents.tools import search_postgres

    where = ""
    if finding_type:
        where = f"WHERE finding_type = '{finding_type}'"

    sql = f"""
        SELECT finding_type, severity, COUNT(*) as count
        FROM findings {where}
        GROUP BY finding_type, severity
        ORDER BY count DESC
        LIMIT 50
    """
    return search_postgres(sql)


@tool_registry.register(tags=["analysis", "dashboard"])
def get_department_risk() -> str:
    """Get risk scores aggregated by department. Shows which departments have the most security findings."""
    from app.agents.tools import search_postgres

    sql = """
        SELECT
            department,
            COUNT(*) as total_findings,
            COUNT(*) FILTER (WHERE severity = 'critical') as critical_count,
            COUNT(*) FILTER (WHERE severity = 'high') as high_count,
            COUNT(*) FILTER (WHERE severity = 'medium') as medium_count,
            COUNT(*) FILTER (WHERE severity = 'low') as low_count
        FROM findings
        GROUP BY department
        ORDER BY critical_count DESC, high_count DESC
        LIMIT 20
    """
    return search_postgres(sql)


@tool_registry.register(tags=["analysis", "dashboard"])
def get_recent_secrets(limit: int = 20) -> str:
    """Get the most recent secrets and PII findings detected in AI conversations.

    Args:
        limit: Number of recent findings to return. Default 20.
    """
    from app.agents.tools import search_postgres

    sql = f"""
        SELECT finding_type, severity, snippet, source_file, created_at
        FROM findings
        WHERE finding_type IN ('secret', 'pii')
        ORDER BY created_at DESC
        LIMIT {min(limit, 100)}
    """
    return search_postgres(sql)


@tool_registry.register(tags=["analysis", "dashboard"])
def get_chat_stats() -> str:
    """Get overall statistics about imported AI chat conversations — total count, models used, sources."""
    from app.agents.tools import search_postgres

    sql = """
        SELECT
            COUNT(*) as total_chats,
            COUNT(DISTINCT source) as source_count,
            COUNT(DISTINCT model) as model_count,
            MIN(created_at) as earliest,
            MAX(created_at) as latest
        FROM chats
    """
    return search_postgres(sql)

