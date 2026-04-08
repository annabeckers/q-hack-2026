"""CLI tool for quick API exploration using configured clients.

Usage:
    uv run python scripts/api_explore.py weather /weather?q=London
    uv run python scripts/api_explore.py github /repos/anthropics/claude-code
    uv run python scripts/api_explore.py custom https://some-api.com/endpoint --header "X-API-Key: abc"
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sys
import time
from pathlib import Path

# Add the backend root to sys.path so `app` package resolves
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.infrastructure.api_client import APIClient, APIClientFactory  # noqa: E402

CACHE_DIR = Path(__file__).resolve().parents[3] / "resources" / "data" / "api-cache"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Quick API exploration tool")
    parser.add_argument("api_name", help="API name from config/apis.yaml, or 'custom'")
    parser.add_argument("endpoint", help="API path (e.g. /weather?q=London) or full URL for custom")
    parser.add_argument("--method", "-m", default="GET", choices=["GET", "POST", "PUT", "PATCH", "DELETE"])
    parser.add_argument("--data", "-d", help="JSON body for POST/PUT/PATCH")
    parser.add_argument("--header", "-H", action="append", default=[], help="Extra header (Key: Value)")
    parser.add_argument("--no-cache", action="store_true", help="Skip response caching")
    parser.add_argument("--save", "-s", action="store_true", default=True, help="Save response to file (default)")
    parser.add_argument("--no-save", action="store_true", help="Do not save response to file")
    return parser.parse_args()


def parse_headers(raw: list[str]) -> dict[str, str]:
    headers = {}
    for h in raw:
        if ":" in h:
            key, val = h.split(":", 1)
            headers[key.strip()] = val.strip()
    return headers


def save_response(api_name: str, endpoint: str, data: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    slug = hashlib.md5(endpoint.encode()).hexdigest()[:12]
    filename = f"{api_name}_{slug}.json"
    path = CACHE_DIR / filename
    path.write_text(data)
    return path


async def run_custom(endpoint: str, method: str, headers: dict, body: str | None) -> None:
    """Hit an arbitrary URL without config."""
    client = APIClient(base_url=endpoint, auth_type="bearer", credentials={})
    start = time.monotonic()

    kwargs: dict = {"headers": headers, "cache": False}
    if body:
        kwargs["json"] = json.loads(body)

    resp = await client.request(method, "", **kwargs)
    elapsed = (time.monotonic() - start) * 1000
    _print_result("custom", endpoint, resp, elapsed)


async def run_configured(
    api_name: str,
    endpoint: str,
    method: str,
    headers: dict,
    body: str | None,
    no_cache: bool,
    no_save: bool,
) -> None:
    """Hit a configured API from apis.yaml."""
    client = APIClientFactory.from_config(api_name)
    extra_headers = {**client.extra_headers, **headers}
    start = time.monotonic()

    kwargs: dict = {"headers": extra_headers, "cache": not no_cache}
    if body:
        kwargs["json"] = json.loads(body)

    resp = await client.request(method, endpoint, **kwargs)
    elapsed = (time.monotonic() - start) * 1000
    _print_result(api_name, endpoint, resp, elapsed, save=not no_save)


def _print_result(api_name: str, endpoint: str, resp, elapsed: float, save: bool = True) -> None:
    """Pretty-print and optionally save the response."""
    print(f"\n{'=' * 60}")
    print(f"  API:      {api_name}")
    print(f"  Endpoint: {endpoint}")
    print(f"  Status:   {resp.status_code}")
    print(f"  Duration: {elapsed:.0f}ms")
    print(f"{'=' * 60}\n")

    try:
        data = resp.json()
        formatted = json.dumps(data, indent=2, ensure_ascii=False)
    except Exception:
        formatted = resp.text if hasattr(resp, "text") else resp.content.decode()
        data = None

    print(formatted[:5000])
    if len(formatted) > 5000:
        print(f"\n... truncated ({len(formatted)} chars total)")

    if save and data is not None:
        path = save_response(api_name, endpoint, formatted)
        print(f"\nSaved to: {path}")


def main() -> None:
    args = parse_args()

    if args.api_name == "custom":
        asyncio.run(run_custom(args.endpoint, args.method, parse_headers(args.header), args.data))
    else:
        asyncio.run(
            run_configured(
                args.api_name,
                args.endpoint,
                args.method,
                parse_headers(args.header),
                args.data,
                args.no_cache,
                args.no_save,
            )
        )


if __name__ == "__main__":
    main()
