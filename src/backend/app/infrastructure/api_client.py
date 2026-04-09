"""Reusable async API client with auth, caching, and rate limiting."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

import httpx
import structlog
import yaml

logger = structlog.get_logger(__name__)


def _find_config_path() -> Path:
    """Search upward from this file for config/apis.yaml."""
    current = Path(__file__).resolve().parent
    for _ in range(10):
        candidate = current / "config" / "apis.yaml"
        if candidate.exists():
            return candidate
        current = current.parent
    # Fallback — won't exist, but APIClientFactory handles missing configs lazily
    return Path("/config/apis.yaml")


_CONFIG_PATH = _find_config_path()


class APIClient:
    """Async HTTP client with pluggable auth, caching, and rate limiting."""

    def __init__(
        self,
        base_url: str,
        auth_type: str = "bearer",
        credentials: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        cache_ttl: int = 0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.auth_type = auth_type
        self.credentials = credentials or {}
        self.extra_headers = headers or {}
        self.cache_ttl = cache_ttl
        self._oauth_token: str | None = None
        self._oauth_expires: float = 0
        self._redis: Any | None = None

    async def _get_redis(self) -> Any | None:
        if self._redis is not None:
            return self._redis
        try:
            import redis.asyncio as aioredis

            self._redis = aioredis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
            await self._redis.ping()
            return self._redis
        except Exception:
            logger.warning("redis_unavailable", msg="caching disabled")
            self._redis = False  # sentinel: tried and failed
            return None

    def _apply_auth(self, kwargs: dict) -> dict:
        headers = {**self.extra_headers, **kwargs.pop("headers", {})}
        params = dict(kwargs.pop("params", {}) or {})

        if self.auth_type == "bearer":
            token = self.credentials.get("token") or os.getenv(self.credentials.get("token_env", ""), "")
            if token:
                headers["Authorization"] = f"Bearer {token}"
        elif self.auth_type == "api_key":
            key = self.credentials.get("key") or os.getenv(self.credentials.get("key_env", ""), "")
            param_name = self.credentials.get("param_name", "api_key")
            if key:
                params[param_name] = key
        elif self.auth_type == "basic":
            user = self.credentials.get("username") or os.getenv(self.credentials.get("username_env", ""), "")
            pw = self.credentials.get("password") or os.getenv(self.credentials.get("password_env", ""), "")
            kwargs["auth"] = (user, pw)
        elif self.auth_type == "oauth2" and self._oauth_token:
            headers["Authorization"] = f"Bearer {self._oauth_token}"

        kwargs["headers"] = headers
        if params:
            kwargs["params"] = params
        return kwargs

    async def _refresh_oauth_token(self) -> None:
        if self.auth_type != "oauth2":
            return
        if self._oauth_token and time.time() < self._oauth_expires - 30:
            return
        token_url = self.credentials.get("token_url", "")
        client_id = os.getenv(self.credentials.get("client_id_env", ""), "")
        client_secret = os.getenv(self.credentials.get("client_secret_env", ""), "")
        scope = self.credentials.get("scope", "")
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "scope": scope,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            self._oauth_token = data["access_token"]
            self._oauth_expires = time.time() + data.get("expires_in", 3600)
            logger.info("oauth2_token_refreshed", expires_in=data.get("expires_in"))

    async def request(self, method: str, path: str, **kwargs) -> httpx.Response:
        """Send request with auth, caching, and rate-limit handling."""
        if self.auth_type == "oauth2":
            await self._refresh_oauth_token()

        url = f"{self.base_url}/{path.lstrip('/')}" if path else self.base_url
        cache = kwargs.pop("cache", self.cache_ttl > 0)
        kwargs = self._apply_auth(kwargs)

        # Check cache for GET requests
        cache_key = None
        if cache and method.upper() == "GET" and self.cache_ttl > 0:
            raw = f"{url}{kwargs.get('params', '')}".encode()
            cache_key = f"api_cache:{hashlib.md5(raw).hexdigest()}"
            redis = await self._get_redis()
            if redis:
                cached = await redis.get(cache_key)
                if cached:
                    logger.info("cache_hit", url=url)
                    return _CachedResponse(cached)

        start = time.monotonic()
        async with httpx.AsyncClient() as client:
            resp = await client.request(method, url, **kwargs)
        duration_ms = (time.monotonic() - start) * 1000
        logger.info(
            "api_request",
            method=method,
            url=url,
            status=resp.status_code,
            duration_ms=round(duration_ms, 1),
        )

        # Retry-After rate limiting
        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", "1"))
            logger.warning("rate_limited", retry_after=retry_after, url=url)
            await asyncio.sleep(retry_after)
            return await self.request(method, path, **kwargs)

        # OAuth2: retry once on 401
        if resp.status_code == 401 and self.auth_type == "oauth2" and self._oauth_token:
            self._oauth_token = None
            await self._refresh_oauth_token()
            kwargs = self._apply_auth(kwargs)
            async with httpx.AsyncClient() as client:
                resp = await client.request(method, url, **kwargs)

        # Store in cache
        if cache_key and resp.status_code < 400:
            redis = await self._get_redis()
            if redis:
                await redis.setex(cache_key, self.cache_ttl, resp.content)
        return resp

    async def get(self, path: str = "", params: dict | None = None, **kw) -> httpx.Response:
        """GET with auth applied."""
        return await self.request("GET", path, params=params, **kw)

    async def post(self, path: str = "", data: dict | None = None, **kw) -> httpx.Response:
        """POST with auth applied."""
        return await self.request("POST", path, json=data, **kw)


class _CachedResponse:
    """Minimal response stand-in for cached content."""

    def __init__(self, content: bytes) -> None:
        self.content, self.status_code, self.headers = content, 200, {}

    def json(self) -> Any:
        return json.loads(self.content)

    @property
    def text(self) -> str:
        return self.content.decode()


class APIClientFactory:
    """Build APIClient instances from config/apis.yaml."""

    _clients: dict[str, APIClient] = {}
    _config: dict | None = None

    @classmethod
    def _load_config(cls) -> dict:
        if cls._config is None:
            path = os.getenv("API_CONFIG_PATH", str(_CONFIG_PATH))
            with open(path) as f:
                cls._config = yaml.safe_load(f)
        return cls._config

    @classmethod
    def from_config(cls, name: str) -> APIClient:
        """Build or retrieve a client configured in apis.yaml."""
        if name in cls._clients:
            return cls._clients[name]
        config = cls._load_config()
        apis = config.get("apis", {})
        if name not in apis:
            raise KeyError(f"API '{name}' not found. Available: {list(apis.keys())}")
        api_cfg = apis[name]
        client = APIClient(
            base_url=api_cfg["base_url"],
            auth_type=api_cfg.get("auth_type", "none"),
            credentials=api_cfg.get("auth_config", {}),
            headers=api_cfg.get("headers", {}),
            cache_ttl=api_cfg.get("cache_ttl", 0),
        )
        cls._clients[name] = client
        return client
