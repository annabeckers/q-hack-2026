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
