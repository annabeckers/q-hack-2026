"""Event bus -- Redis-backed pub/sub with list persistence.

Provides real-time event distribution via Redis pub/sub channels
and durable event storage via Redis lists for replay/audit.
"""

import asyncio
import json
from dataclasses import asdict
from typing import Any, Callable, Coroutine

import structlog
from redis.asyncio import Redis

from app.config import settings

log = structlog.get_logger()

# Standard channels
CHANNEL_EVENTS = "agent:events"
CHANNEL_DECISIONS = "agent:decisions"
CHANNEL_APPROVALS = "agent:approvals"
CHANNEL_ALERTS = "system:alerts"


class EventBus:
    """Redis-backed event bus with pub/sub and list persistence.

    Usage:
        bus = EventBus()
        await bus.publish("agent:events", {"type": "task", "payload": {...}})
        await bus.subscribe("agent:events", my_handler)
    """

    def __init__(self, redis: Redis | None = None):
        self._redis = redis
        self._subscribers: dict[str, list[Callable]] = {}
        self._listener_tasks: list[asyncio.Task] = []
        self._running = False

    async def _get_redis(self) -> Redis:
        if not self._redis:
            self._redis = Redis.from_url(settings.redis_url, decode_responses=True)
        return self._redis

    async def publish(self, channel: str, event: dict | Any) -> None:
        """Publish event to channel (pub/sub + list persistence)."""
        r = await self._get_redis()
        data = event if isinstance(event, str) else json.dumps(
            asdict(event) if hasattr(event, "__dataclass_fields__") else event
        )

        # Persist to list for durability / replay
        await r.rpush(f"{channel}:log", data)
        await r.ltrim(f"{channel}:log", -1000, -1)

        # Broadcast via pub/sub for real-time
        await r.publish(channel, data)
        log.debug("event_published", channel=channel)

    async def subscribe(
        self,
        channel: str,
        callback: Callable[[dict], Coroutine],
    ) -> None:
        """Subscribe to a channel. Callback receives parsed JSON dicts."""
        if channel not in self._subscribers:
            self._subscribers[channel] = []
        self._subscribers[channel].append(callback)

        if self._running:
            task = asyncio.create_task(self._listen(channel))
            self._listener_tasks.append(task)

    async def _listen(self, channel: str) -> None:
        """Internal listener loop for a single channel."""
        r = await self._get_redis()
        pubsub = r.pubsub()
        await pubsub.subscribe(channel)
        log.info("event_bus_listening", channel=channel)

        try:
            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue
                data = json.loads(message["data"])
                for cb in self._subscribers.get(channel, []):
                    try:
                        await cb(data)
                    except Exception as e:
                        log.error("subscriber_error", channel=channel, error=str(e))
        except asyncio.CancelledError:
            await pubsub.unsubscribe(channel)
            await pubsub.close()

    async def start(self) -> None:
        """Start all registered listener loops."""
        self._running = True
        for channel in self._subscribers:
            task = asyncio.create_task(self._listen(channel))
            self._listener_tasks.append(task)
        log.info("event_bus_started", channels=list(self._subscribers.keys()))

    async def stop(self) -> None:
        """Cancel all listener tasks."""
        self._running = False
        for task in self._listener_tasks:
            task.cancel()
        if self._listener_tasks:
            await asyncio.gather(*self._listener_tasks, return_exceptions=True)
        self._listener_tasks.clear()
        log.info("event_bus_stopped")

    async def get_log(self, channel: str, limit: int = 50) -> list[dict]:
        """Read recent events from persistent log."""
        r = await self._get_redis()
        raw = await r.lrange(f"{channel}:log", -limit, -1)
        return [json.loads(item) for item in raw]
