"""Agent memory — Redis-backed conversation history and session state.

Provides persistent memory across agent interactions. Each session
maintains a conversation history and optional key-value context.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone

from redis.asyncio import Redis

from app.config import settings


@dataclass
class AgentMessage:
    role: str  # "user", "assistant", "system", "tool"
    content: str
    agent: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AgentMemory:
    """Redis-backed agent conversation memory.

    Usage:
        memory = AgentMemory(redis_client)
        await memory.add("session-123", AgentMessage(role="user", content="Hello"))
        history = await memory.get_history("session-123")
        await memory.set_context("session-123", "user_name", "Lars")
    """

    def __init__(self, redis: Redis | None = None):
        self._redis = redis

    async def _get_redis(self) -> Redis:
        if not self._redis:
            self._redis = Redis.from_url(settings.redis_url, decode_responses=True)
        return self._redis

    async def add(self, session_id: str, message: AgentMessage) -> None:
        """Append a message to the session history."""
        r = await self._get_redis()
        key = f"agent:history:{session_id}"
        await r.rpush(key, json.dumps({
            "role": message.role,
            "content": message.content,
            "agent": message.agent,
            "timestamp": message.timestamp,
        }))
        # Keep last 200 messages per session
        await r.ltrim(key, -200, -1)
        # Expire after 24h
        await r.expire(key, 86400)

    async def get_history(self, session_id: str, limit: int = 50) -> list[AgentMessage]:
        """Get recent conversation history."""
        r = await self._get_redis()
        key = f"agent:history:{session_id}"
        raw = await r.lrange(key, -limit, -1)
        return [AgentMessage(**json.loads(m)) for m in raw]

    async def set_context(self, session_id: str, key: str, value: str) -> None:
        """Set a key-value context for the session."""
        r = await self._get_redis()
        ctx_key = f"agent:context:{session_id}"
        await r.hset(ctx_key, key, value)
        await r.expire(ctx_key, 86400)

    async def get_context(self, session_id: str) -> dict[str, str]:
        """Get all context for a session."""
        r = await self._get_redis()
        ctx_key = f"agent:context:{session_id}"
        return await r.hgetall(ctx_key)

    async def clear(self, session_id: str) -> None:
        """Clear all memory for a session."""
        r = await self._get_redis()
        await r.delete(f"agent:history:{session_id}", f"agent:context:{session_id}")
