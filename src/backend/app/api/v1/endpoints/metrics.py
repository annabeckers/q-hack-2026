"""Prometheus-compatible metrics endpoint."""

import time
from fastapi import APIRouter, Request

router = APIRouter()

# Simple in-memory counters. For production, use prometheus_client library.
_metrics = {
    "requests_total": 0,
    "requests_by_status": {},
    "agent_invocations": 0,
    "upload_count": 0,
    "startup_time": time.time(),
}


def inc_request(status_code: int) -> None:
    _metrics["requests_total"] += 1
    key = str(status_code)
    _metrics["requests_by_status"][key] = _metrics["requests_by_status"].get(key, 0) + 1


def inc_agent() -> None:
    _metrics["agent_invocations"] += 1


def inc_upload() -> None:
    _metrics["upload_count"] += 1


@router.get("/metrics")
async def metrics():
    """Prometheus-style metrics in JSON. Wire to /metrics for Grafana."""
    uptime = time.time() - _metrics["startup_time"]
    return {
        "uptime_seconds": round(uptime),
        "requests_total": _metrics["requests_total"],
        "requests_by_status": _metrics["requests_by_status"],
        "agent_invocations": _metrics["agent_invocations"],
        "upload_count": _metrics["upload_count"],
    }
