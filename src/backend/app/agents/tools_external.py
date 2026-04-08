"""Pre-built agent tools for common external API interactions.

Each tool returns a JSON string for agent framework compatibility.
Uses APIClient/APIClientFactory for auth, caching, and rate limiting.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from app.infrastructure.api_client import APIClient, APIClientFactory


def _run(coro) -> Any:
    """Run async code from sync tool context."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor() as pool:
        return loop.run_in_executor(pool, asyncio.run, coro)


async def _async_get_weather(location: str) -> str:
    """Fetch weather data from OpenWeatherMap."""
    client = APIClientFactory.from_config("weather")
    resp = await client.get("/weather", params={"q": location, "units": "metric"})
    if resp.status_code != 200:
        return json.dumps({"error": f"Weather API returned {resp.status_code}", "body": resp.text[:500]})
    data = resp.json()
    return json.dumps(
        {
            "location": data.get("name", location),
            "temperature_c": data.get("main", {}).get("temp"),
            "feels_like_c": data.get("main", {}).get("feels_like"),
            "humidity": data.get("main", {}).get("humidity"),
            "description": data.get("weather", [{}])[0].get("description", ""),
            "wind_speed_ms": data.get("wind", {}).get("speed"),
        },
        indent=2,
    )


def get_weather(location: str) -> str:
    """Get current weather data for a location.

    Args:
        location: City name, e.g. 'London' or 'Berlin,DE'.

    Returns:
        JSON string with temperature, humidity, description, wind speed.
    """
    return asyncio.run(_async_get_weather(location))


async def _async_search_web(query: str) -> str:
    """Search the web via SerpAPI or similar search API."""
    import os

    api_key = os.getenv("SERPAPI_KEY", "")
    if not api_key:
        return json.dumps({"error": "SERPAPI_KEY not set. Set it in .env to enable web search."})

    client = APIClient(
        base_url="https://serpapi.com",
        auth_type="api_key",
        credentials={"param_name": "api_key", "key": api_key},
        cache_ttl=300,
    )
    resp = await client.get("/search", params={"q": query, "engine": "google", "num": 5})
    if resp.status_code != 200:
        return json.dumps({"error": f"Search API returned {resp.status_code}"})
    data = resp.json()
    results = []
    for item in data.get("organic_results", [])[:5]:
        results.append(
            {
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "snippet": item.get("snippet", ""),
            }
        )
    return json.dumps(results, indent=2)


def search_web(query: str) -> str:
    """Search the web and return top results.

    Args:
        query: Search query string.

    Returns:
        JSON string with list of {title, link, snippet} results.
    """
    return asyncio.run(_async_search_web(query))


async def _async_fetch_url(url: str) -> str:
    """Fetch content from a URL and extract text."""
    client = APIClient(base_url=url, auth_type="bearer", credentials={})
    resp = await client.request("GET", "", cache=False)
    content_type = resp.headers.get("content-type", "")

    if "json" in content_type:
        return json.dumps({"url": url, "content_type": "json", "data": resp.json()}, indent=2)

    text = resp.text[:10000] if hasattr(resp, "text") else resp.content.decode()[:10000]
    # Strip HTML tags for readability
    import re

    clean = re.sub(r"<[^>]+>", " ", text)
    clean = re.sub(r"\s+", " ", clean).strip()

    return json.dumps(
        {
            "url": url,
            "status": resp.status_code,
            "content_type": content_type.split(";")[0],
            "text": clean[:5000],
        },
        indent=2,
    )


def fetch_url(url: str) -> str:
    """Fetch and extract content from a URL.

    Args:
        url: The full URL to fetch.

    Returns:
        JSON string with url, status, content_type, and extracted text or data.
    """
    return asyncio.run(_async_fetch_url(url))


def compare_datasets(dataset_a: str, dataset_b: str) -> str:
    """Compare two JSON datasets and report differences.

    Args:
        dataset_a: First JSON string or list/dict.
        dataset_b: Second JSON string or list/dict.

    Returns:
        JSON string describing keys added, removed, and changed.
    """
    a = json.loads(dataset_a) if isinstance(dataset_a, str) else dataset_a
    b = json.loads(dataset_b) if isinstance(dataset_b, str) else dataset_b

    if isinstance(a, dict) and isinstance(b, dict):
        keys_a, keys_b = set(a.keys()), set(b.keys())
        added = list(keys_b - keys_a)
        removed = list(keys_a - keys_b)
        changed = [k for k in keys_a & keys_b if a[k] != b[k]]
        return json.dumps(
            {
                "type": "dict_diff",
                "keys_added": added,
                "keys_removed": removed,
                "keys_changed": changed,
                "total_changes": len(added) + len(removed) + len(changed),
            },
            indent=2,
        )

    if isinstance(a, list) and isinstance(b, list):
        return json.dumps(
            {
                "type": "list_diff",
                "length_a": len(a),
                "length_b": len(b),
                "items_only_in_a": len(a) - len(b) if len(a) > len(b) else 0,
                "items_only_in_b": len(b) - len(a) if len(b) > len(a) else 0,
            },
            indent=2,
        )

    return json.dumps({"type": "type_mismatch", "type_a": type(a).__name__, "type_b": type(b).__name__}, indent=2)


async def _async_call_api(api_name: str, endpoint: str, method: str = "GET", params: dict | None = None) -> str:
    """Generic API call using configured client."""
    client = APIClientFactory.from_config(api_name)
    if method.upper() in ("POST", "PUT", "PATCH"):
        resp = await client.request(method.upper(), endpoint, json=params)
    else:
        resp = await client.request(method.upper(), endpoint, params=params)
    try:
        data = resp.json()
    except Exception:
        data = resp.text[:2000] if hasattr(resp, "text") else resp.content.decode()[:2000]
    return json.dumps({"status": resp.status_code, "data": data}, indent=2)


def call_api(api_name: str, endpoint: str, method: str = "GET", params: dict | None = None) -> str:
    """Call any API configured in apis.yaml.

    Args:
        api_name: Name of the API in config/apis.yaml (e.g. 'github', 'weather').
        endpoint: API path (e.g. '/repos/anthropics/claude-code').
        method: HTTP method (GET, POST, PUT, PATCH, DELETE).
        params: Query params for GET, JSON body for POST/PUT/PATCH.

    Returns:
        JSON string with {status, data} from the API response.
    """
    return asyncio.run(_async_call_api(api_name, endpoint, method, params))
