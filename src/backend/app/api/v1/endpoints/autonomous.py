"""Autonomous agent system API -- events, proposals, decisions, supervisor control."""

import json
from dataclasses import asdict

import structlog
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from redis.asyncio import Redis

from app.agents.autonomous import AgentDecision, AgentEvent, AgentSupervisor
from app.agents.memory import AgentMemory
from app.agents.orchestrator import AgentOrchestrator
from app.config import settings

log = structlog.get_logger()
router = APIRouter()

# Module-level supervisor (singleton per process)
_supervisor: AgentSupervisor | None = None


def _get_supervisor() -> AgentSupervisor:
    global _supervisor
    if _supervisor is None:
        orchestrator = AgentOrchestrator.from_yaml()
        memory = AgentMemory()
        _supervisor = AgentSupervisor(orchestrator, memory, mode="autonomous")
    return _supervisor


# --- Request / Response models ---


class EventIn(BaseModel):
    type: str = Field(..., description="Event type identifier")
    payload: dict = Field(default_factory=dict)
    source: str = "api"


class RejectIn(BaseModel):
    reason: str = ""


class ModeIn(BaseModel):
    mode: str = Field("autonomous", pattern="^(autonomous|human_in_loop)$")


# --- Endpoints ---


@router.post("/events", status_code=202)
async def push_event(body: EventIn):
    """Push an event into the autonomous agent pipeline."""
    supervisor = _get_supervisor()
    event = AgentEvent(type=body.type, payload=body.payload, source=body.source)

    if supervisor._running:
        await supervisor.emit_event(event)
        return {"status": "queued", "event_id": event.id}

    # If supervisor is stopped, process inline as one-shot
    decision = await supervisor.process_event(event)
    return {"status": "processed", "event_id": event.id, "decision_id": decision.id}


@router.get("/proposals")
async def list_proposals():
    """List pending proposals awaiting human approval."""
    r = Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        raw = await r.hgetall("agent:proposals")
        proposals = [json.loads(v) for v in raw.values()]
        return {"proposals": proposals, "count": len(proposals)}
    finally:
        await r.close()


@router.post("/proposals/{proposal_id}/approve")
async def approve_proposal(proposal_id: str):
    """Approve a pending proposal for execution."""
    supervisor = _get_supervisor()
    decision = await supervisor.approve(proposal_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return {"status": "approved", "decision": asdict(decision)}


@router.post("/proposals/{proposal_id}/reject")
async def reject_proposal(proposal_id: str, body: RejectIn):
    """Reject a pending proposal with optional reason."""
    supervisor = _get_supervisor()
    decision = await supervisor.reject(proposal_id, reason=body.reason)
    if not decision:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return {"status": "rejected", "decision": asdict(decision)}


@router.get("/decisions")
async def list_decisions(limit: int = 50):
    """List recent decisions from the audit log."""
    r = Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        raw = await r.lrange("agent:decisions:log", -limit, -1)
        decisions = [json.loads(item) for item in raw]
        return {"decisions": decisions, "count": len(decisions)}
    finally:
        await r.close()


@router.post("/start")
async def start_supervisor(body: ModeIn | None = None):
    """Start the autonomous supervisor loop."""
    supervisor = _get_supervisor()
    if supervisor._running:
        return {"status": "already_running", **supervisor.status()}
    if body and body.mode:
        supervisor.mode = body.mode
    await supervisor.start()
    return {"status": "started", **supervisor.status()}


@router.post("/stop")
async def stop_supervisor():
    """Stop the autonomous supervisor loop."""
    supervisor = _get_supervisor()
    if not supervisor._running:
        return {"status": "already_stopped"}
    await supervisor.stop()
    return {"status": "stopped", "events_processed": supervisor._events_processed}


@router.get("/status")
async def get_status():
    """Get current supervisor status."""
    supervisor = _get_supervisor()
    return supervisor.status()
