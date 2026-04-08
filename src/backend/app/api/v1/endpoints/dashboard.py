from __future__ import annotations

import asyncio
import json
from datetime import datetime

from fastapi import APIRouter, Body, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.application.services.deterministic_analysis import default_deterministic_analysis_service
from app.application.services.dashboard_service import default_dashboard_service
from app.domain.dashboard import DashboardFilters

router = APIRouter()


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def _filters(
    dimension: str = "department",
    metric: str = "avgWordCountPerSession",
    time_range: str = "month",
    department: str | None = None,
    model: str | None = None,
    provider: str | None = None,
    category: str | None = None,
    severity: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
    sort_by: str = "timestamp",
    start_date: str | None = None,
    end_date: str | None = None,
) -> DashboardFilters:
    return DashboardFilters(
        time_range=time_range,
        dimension=dimension,
        metric=metric,
        start_date=_parse_datetime(start_date),
        end_date=_parse_datetime(end_date),
        department=department,
        model=model,
        provider=provider,
        category=category,
        severity=severity,
        status=status,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
    )


async def _ensure_deterministic_analysis() -> None:
    await default_deterministic_analysis_service.ensure_completed()


@router.get("/summary")
async def summary(time_range: str = Query("month"), department: str | None = None):
    await _ensure_deterministic_analysis()
    return default_dashboard_service.summary(time_range=time_range, department=department)


@router.get("/summary/compliance-gauge")
async def compliance_gauge(department: str | None = None):
    await _ensure_deterministic_analysis()
    return default_dashboard_service.compliance_score(DashboardFilters(department=department))


@router.get("/analytics/cost")
async def cost_analytics(dimension: str = Query(...), cost_basis: str = Query("per_session"), limit: int = 20, startDate: str | None = None, endDate: str | None = None, department: str | None = None):
    await _ensure_deterministic_analysis()
    if cost_basis != "per_session":
        raise HTTPException(status_code=400, detail="cost_basis must be per_session")
    return default_dashboard_service.cost_analytics(_filters(dimension=dimension, department=department, limit=limit, start_date=startDate, end_date=endDate))


@router.get("/analytics/usage")
async def usage_analytics(dimension: str = Query(...), metric: str = Query("avgWordCountPerSession"), startDate: str | None = None, endDate: str | None = None, department: str | None = None):
    await _ensure_deterministic_analysis()
    return default_dashboard_service.usage_analytics(_filters(dimension=dimension, metric=metric, department=department, start_date=startDate, end_date=endDate))


@router.get("/analytics/model-comparison")
async def model_comparison(department: str | None = None):
    await _ensure_deterministic_analysis()
    return default_dashboard_service.model_comparison(_filters(department=department))


@router.get("/security/findings")
async def findings(type: str = Query("all"), severity: str = Query("all"), status: str = Query("open"), department: str | None = None, provider: str | None = None, limit: int = 100, offset: int = 0):
    await _ensure_deterministic_analysis()
    filters = _filters(category=None if type == "all" else type, severity=None if severity == "all" else severity, status=status, department=department, provider=provider, limit=limit, offset=offset)
    return default_dashboard_service.findings(filters)


@router.get("/security/findings/{finding_id}")
async def finding_detail(finding_id: str):
    await _ensure_deterministic_analysis()
    finding = default_dashboard_service.finding_detail(finding_id)
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    return finding


@router.patch("/security/findings/{finding_id}/remediation")
async def finding_remediation(finding_id: str, body: dict = Body(...)):
    await _ensure_deterministic_analysis()
    status = str(body.get("status") or "").strip()
    notes = body.get("notes")
    if status not in {"acknowledged", "resolved"}:
        raise HTTPException(status_code=400, detail="status must be acknowledged or resolved")
    updated = default_dashboard_service.update_finding_status(finding_id, status, notes)
    if not updated:
        raise HTTPException(status_code=404, detail="Finding not found")
    return updated


@router.get("/security/severity-distribution")
async def severity_distribution(department: str | None = None, provider: str | None = None):
    await _ensure_deterministic_analysis()
    return default_dashboard_service.severity_distribution(_filters(department=department, provider=provider))


@router.get("/security/leak-counts")
async def leak_counts(model: str | None = None, category: str | None = None, department: str | None = None):
    await _ensure_deterministic_analysis()
    return default_dashboard_service.leak_counts(_filters(model=model, category=category, department=department))


@router.get("/security/slopsquatting")
async def slopsquatting(dimension: str = Query("model"), sortBy: str = Query("count"), department: str | None = None):
    await _ensure_deterministic_analysis()
    return default_dashboard_service.slopsquatting(_filters(dimension=dimension, sort_by=sortBy, department=department))


@router.get("/security/duplicate-secrets")
async def duplicate_secrets(minUsers: int = 2, department: str | None = None):
    await _ensure_deterministic_analysis()
    findings = default_dashboard_service.duplicate_secrets(_filters(department=department))
    return [finding for finding in findings if finding["affectedUsers"] >= minUsers]


@router.get("/trends/timeseries")
async def time_series(metric: str, granularity: str = Query("day"), department: str | None = None, startDate: str | None = None, endDate: str | None = None):
    await _ensure_deterministic_analysis()
    return default_dashboard_service.time_series(_filters(dimension=granularity, metric=metric, department=department, start_date=startDate, end_date=endDate))


@router.get("/trends/anomalies")
async def anomalies(department: str | None = None, zscore: float = 2.0):
    await _ensure_deterministic_analysis()
    return [alert for alert in default_dashboard_service.anomalies(_filters(department=department)) if abs(alert["zScore"]) >= zscore]


@router.get("/trends/patterns-by-time")
async def patterns_by_time(department: str | None = None):
    await _ensure_deterministic_analysis()
    return default_dashboard_service.patterns_by_time(_filters(department=department))


@router.get("/trends/complexity-scatter")
async def complexity_scatter(department: str | None = None, provider: str | None = None):
    await _ensure_deterministic_analysis()
    return default_dashboard_service.complexity_scatter(_filters(department=department, provider=provider))


@router.get("/alerts")
async def alerts(since: str | None = None, severity: str | None = None, type: str | None = None, limit: int = 50, department: str | None = None):
    await _ensure_deterministic_analysis()
    return default_dashboard_service.alerts(_filters(department=department, severity=severity, category=type, limit=limit))


@router.get("/alerts/stream")
async def alert_stream(severity: str | None = None):
    await _ensure_deterministic_analysis()

    async def generator():
        for alert in default_dashboard_service.alerts(_filters(severity=severity, limit=50)):
            yield f"data: {json.dumps(alert, default=str)}\n\n"
            await asyncio.sleep(0)

    return StreamingResponse(generator(), media_type="text/event-stream")


@router.post("/alerts/{finding_id}/acknowledge")
async def acknowledge_alert(finding_id: str, body: dict = Body(default_factory=dict)):
    await _ensure_deterministic_analysis()
    updated = default_dashboard_service.acknowledge_alert(finding_id, str(body.get("notes") or "") or None)
    if not updated:
        raise HTTPException(status_code=404, detail="Alert not found")
    return updated
