"""Autonomous agent supervisor -- event-driven multi-agent loop.

Runs continuously, processing events from Redis and routing them
through the orchestrator pipeline. Supports fully autonomous execution
or human-in-the-loop approval gates.
"""

import asyncio
import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

import structlog
from redis.asyncio import Redis

from app.agents.event_bus import CHANNEL_DECISIONS, CHANNEL_EVENTS, EventBus
from app.agents.memory import AgentMemory
from app.agents.orchestrator import AgentOrchestrator
from app.config import settings

log = structlog.get_logger()


@dataclass
class AgentEvent:
    type: str
    payload: dict
    source: str = "api"
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class AgentDecision:
    event_id: str
    decision: str
    reasoning: str
    approved: bool = False
    executed: bool = False
    rejected_reason: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AgentSupervisor:
    """Event-driven agent supervisor with optional human-in-the-loop.

    Modes:
        autonomous    -- process and execute decisions immediately
        human_in_loop -- propose decisions, wait for human approval

    Usage:
        supervisor = AgentSupervisor(orchestrator, memory, mode="autonomous")
        await supervisor.start()
    """

    def __init__(
        self,
        orchestrator: AgentOrchestrator,
        memory: AgentMemory,
        mode: str = "autonomous",
    ):
        self.orchestrator = orchestrator
        self.memory = memory
        self.mode = mode
        self.event_bus = EventBus()
        self._running = False
        self._task: asyncio.Task | None = None
        self._redis: Redis | None = None
        self._started_at: str | None = None
        self._events_processed: int = 0

    async def _get_redis(self) -> Redis:
        if not self._redis:
            self._redis = Redis.from_url(settings.redis_url, decode_responses=True)
        return self._redis

    async def start(self) -> None:
        """Begin the event processing loop."""
        if self._running:
            log.warning("supervisor_already_running")
            return
        self._running = True
        self._started_at = datetime.now(timezone.utc).isoformat()
        self._task = asyncio.create_task(self._loop())
        await self.event_bus.start()
        log.info("supervisor_started", mode=self.mode)

    async def stop(self) -> None:
        """Graceful shutdown."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self.event_bus.stop()
        log.info("supervisor_stopped", events_processed=self._events_processed)

    async def _loop(self) -> None:
        """Main event loop -- pops events from Redis list."""
        r = await self._get_redis()
        while self._running:
            try:
                result = await r.blpop(CHANNEL_EVENTS, timeout=2)
                if result is None:
                    continue
                _, raw = result
                event_data = json.loads(raw)
                event = AgentEvent(**event_data)
                await self.process_event(event)
            except asyncio.CancelledError:
                break
            except Exception as e:
                log.error("supervisor_loop_error", error=str(e))
                await asyncio.sleep(1)

    async def process_event(self, event: AgentEvent) -> AgentDecision:
        """Run orchestrator on event, produce a decision."""
        log.info("processing_event", event_id=event.id, type=event.type)
        self._events_processed += 1

        session = await self.orchestrator.run(
            trigger=f"[{event.type}] {json.dumps(event.payload)}",
            context={"source": event.source, "event_id": event.id},
        )

        reasoning = " | ".join(r.content[:200] for r in session.responses)
        decision = AgentDecision(
            event_id=event.id,
            decision=session.decision,
            reasoning=reasoning,
        )

        if self.mode == "autonomous":
            decision.approved = True
            decision.executed = True
            await self._store_decision(decision)
            log.info("decision_auto_executed", decision_id=decision.id)
        else:
            await self.propose(decision)

        await self.event_bus.publish(CHANNEL_DECISIONS, decision)
        return decision

    async def propose(self, decision: AgentDecision) -> None:
        """Store decision as pending proposal for human review."""
        r = await self._get_redis()
        await r.hset("agent:proposals", decision.id, json.dumps(asdict(decision)))
        log.info("decision_proposed", decision_id=decision.id)

    async def approve(self, decision_id: str) -> AgentDecision | None:
        """Human approves a pending proposal."""
        r = await self._get_redis()
        raw = await r.hget("agent:proposals", decision_id)
        if not raw:
            return None
        decision = AgentDecision(**json.loads(raw))
        decision.approved = True
        decision.executed = True
        await r.hdel("agent:proposals", decision_id)
        await self._store_decision(decision)
        log.info("decision_approved", decision_id=decision_id)
        return decision

    async def reject(self, decision_id: str, reason: str = "") -> AgentDecision | None:
        """Human rejects a pending proposal."""
        r = await self._get_redis()
        raw = await r.hget("agent:proposals", decision_id)
        if not raw:
            return None
        decision = AgentDecision(**json.loads(raw))
        decision.rejected_reason = reason
        await r.hdel("agent:proposals", decision_id)
        await self._store_decision(decision)
        log.info("decision_rejected", decision_id=decision_id, reason=reason)
        return decision

    async def emit_event(self, event: AgentEvent) -> None:
        """Push an event onto the queue for processing."""
        r = await self._get_redis()
        await r.rpush(CHANNEL_EVENTS, json.dumps(asdict(event)))
        log.info("event_emitted", event_id=event.id, type=event.type)

    async def _store_decision(self, decision: AgentDecision) -> None:
        """Persist decision to audit log."""
        r = await self._get_redis()
        await r.rpush("agent:decisions:log", json.dumps(asdict(decision)))
        await r.ltrim("agent:decisions:log", -500, -1)

    def status(self) -> dict:
        """Current supervisor status."""
        return {
            "running": self._running,
            "mode": self.mode,
            "started_at": self._started_at,
            "events_processed": self._events_processed,
        }
