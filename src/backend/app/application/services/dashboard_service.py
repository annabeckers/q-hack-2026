from __future__ import annotations

import hashlib
from collections import Counter, defaultdict
from datetime import datetime, timezone
from statistics import mean, pstdev

from app.domain.dashboard import DashboardFilters, FindingRecord, UsageRecord
from app.infrastructure.repositories.dashboard_repository import DashboardRepository, default_dashboard_repository
from app.infrastructure.repositories.deterministic_analysis_repository import DeterministicAnalysisRepository
from app.infrastructure.database import async_session_factory


def _family(name: str | None) -> str:
    lower = (name or "unknown").strip().lower()
    if lower.startswith(("gpt", "openai", "o1", "o3")):
        return "chatgpt"
    if lower.startswith("claude"):
        return "anthropic"
    if lower.startswith("gemini"):
        return "gemini"
    if lower.startswith("mistral"):
        return "mistral"
    return lower


def _is_trivial(record: UsageRecord) -> bool:
    purpose = record.purpose.lower()
    if record.token_count > 500:
        return False
    return any(keyword in purpose for keyword in ["what time", "weather", "wetter", "recipe", "joke", "was ist", "what is"])


def _is_private(record: UsageRecord) -> bool:
    purpose = record.purpose.lower()
    return any(keyword in purpose for keyword in ["cv", "bewerbung", "relationship", "vacation", "loan", "mortgage", "rezept", "travel"])


class DashboardService:
    def __init__(self, repository: DashboardRepository = default_dashboard_repository):
        self._repository = repository

    def _filter_usage(self, filters: DashboardFilters, *, require_data: bool = False) -> list[UsageRecord]:
        records = self._repository.list_usage_records(raise_on_missing=require_data)
        if filters.department:
            records = [record for record in records if record.department_id == filters.department]
        if filters.model:
            records = [record for record in records if record.model_name == filters.model]
        if filters.provider:
            provider = filters.provider.lower()
            records = [record for record in records if _family(record.model_name) == provider or _family(record.tool_name) == provider]
        if filters.start_date:
            records = [record for record in records if record.usage_start >= filters.start_date]
        if filters.end_date:
            records = [record for record in records if record.usage_end <= filters.end_date]
        return records

    def _filter_findings(self, filters: DashboardFilters) -> list[FindingRecord]:
        records = self._repository.list_findings()
        if filters.department:
            records = [record for record in records if record.department == filters.department]
        if filters.model:
            records = [record for record in records if record.model == filters.model]
        if filters.provider:
            provider = filters.provider.lower()
            records = [record for record in records if record.provider == provider]
        if filters.category:
            records = [record for record in records if record.type == filters.category or record.category == filters.category]
        if filters.severity:
            records = [record for record in records if record.severity == filters.severity]
        if filters.status:
            records = [record for record in records if record.status == filters.status]
        if filters.start_date:
            records = [record for record in records if record.timestamp >= filters.start_date]
        if filters.end_date:
            records = [record for record in records if record.timestamp <= filters.end_date]
        return records

    def summary(self, time_range: str = "month", department: str | None = None) -> dict:
        filters = DashboardFilters(time_range=time_range, department=department)
        usage = self._filter_usage(filters)
        findings = self._filter_findings(filters)
        compliance = self.compliance_score(filters)
        departments = Counter(record.department_id for record in usage)
        top_departments = [
            {"department": department_name, "cost": round(sum(record.cost for record in usage if record.department_id == department_name), 4), "events": count}
            for department_name, count in departments.most_common(5)
        ]

        return {
            "period": time_range,
            "generatedAt": datetime.now(timezone.utc),
            "metrics": {
                "totalCost": round(sum(record.cost for record in usage), 4),
                "totalEvents": len(usage),
                "totalTokens": sum(record.token_count for record in usage),
                "totalDepartments": len({record.department_id for record in usage}),
                "totalModels": len({record.model_name for record in usage}),
            },
            "findings": {
                "totalFindings": len(findings),
                "criticalCount": sum(1 for finding in findings if finding.severity == "critical"),
                "highCount": sum(1 for finding in findings if finding.severity == "high"),
                "mediumCount": sum(1 for finding in findings if finding.severity == "medium"),
                "categoryCounts": {
                    "secrets": sum(1 for finding in findings if finding.type == "secret"),
                    "pii": sum(1 for finding in findings if finding.type == "pii"),
                    "slopsquat": sum(1 for finding in findings if finding.type == "slopsquat"),
                },
            },
            "compliance": {
                "complianceScore": compliance["overallScore"],
                "status": compliance["status"],
            },
            "anomalies": len(self.anomalies(filters)),
            "topDepartments": top_departments,
        }

    def compliance_score(self, filters: DashboardFilters | None = None) -> dict:
        usage = self._filter_usage(filters or DashboardFilters())
        if not usage:
            return {"overallScore": 0, "status": "non_compliant", "auditPillars": [], "lastAudited": datetime.now(timezone.utc)}

        checks = {
            "purpose_logged": sum(1 for record in usage if record.purpose),
            "region_logged": sum(1 for record in usage if record.region),
            "model_name_logged": sum(1 for record in usage if record.model_name),
            "department_attributed": sum(1 for record in usage if record.department_id),
            "user_pseudonymized": sum(1 for record in usage if record.user_id_hash),
        }
        total = len(usage)
        details = []
        for check, count in checks.items():
            pct = int((count / total) * 100) if total else 0
            details.append({"check": check, "description": check.replace("_", " "), "compliancePercentage": pct, "recordsCovering": count, "totalRecords": total})
        overall = round(sum(item["compliancePercentage"] for item in details) / len(details)) if details else 0
        status = "compliant" if overall >= 80 else "partial" if overall >= 50 else "non_compliant"
        return {"overallScore": overall, "status": status, "auditPillars": details, "lastAudited": datetime.now(timezone.utc)}

    def _bucket_key(self, record: UsageRecord, dimension: str) -> str:
        if dimension == "department":
            return record.department_id
        if dimension == "model":
            return record.model_name
        if dimension == "tool":
            return record.tool_name
        if dimension == "region":
            return record.region or "unknown"
        if dimension == "timespan":
            return record.usage_start.strftime("%Y-%m-%d")
        return "unknown"

    def cost_analytics(self, filters: DashboardFilters) -> dict:
        usage = self._filter_usage(filters, require_data=True)
        buckets: dict[str, dict[str, float | int]] = defaultdict(lambda: {"cost": 0.0, "sessions": 0, "tokens": 0, "trivial": 0, "private": 0})

        for record in usage:
            key = self._bucket_key(record, filters.dimension)
            bucket = buckets[key]
            bucket["cost"] += record.cost
            bucket["sessions"] += 1
            bucket["tokens"] += record.token_count
            bucket["trivial"] += 1 if _is_trivial(record) else 0
            bucket["private"] += 1 if _is_private(record) else 0

        items = []
        for key, bucket in sorted(buckets.items(), key=lambda item: -float(item[1]["cost"])):
            sessions = int(bucket["sessions"]) or 1
            tokens = int(bucket["tokens"]) or 1
            items.append({
                "key": key,
                "cost": round(float(bucket["cost"]), 4),
                "sessions": int(bucket["sessions"]),
                "avgCostPerSession": round(float(bucket["cost"]) / sessions, 4),
                "events": int(bucket["sessions"]),
                "tokens": int(bucket["tokens"]),
                "costPerToken": round(float(bucket["cost"]) / tokens, 6),
                "trivialPercentage": round((int(bucket["trivial"]) / sessions) * 100, 2),
                "privatePercentage": round((int(bucket["private"]) / sessions) * 100, 2),
            })

        return {"costBasis": "per_session", "dimension": filters.dimension, "items": items, "total": round(sum(record.cost for record in usage), 4), "totalRecords": len(usage)}

    def usage_analytics(self, filters: DashboardFilters) -> dict:
        usage = self._filter_usage(filters, require_data=True)
        buckets: dict[str, list[UsageRecord]] = defaultdict(list)
        for record in usage:
            buckets[self._bucket_key(record, filters.dimension)].append(record)

        items = []
        for key, records in sorted(buckets.items(), key=lambda item: -sum(record.token_count for record in item[1])):
            sessions = len(records) or 1
            items.append({
                "key": key,
                "events": len(records),
                "tokens": sum(record.token_count for record in records),
                "sessions": sessions,
                "averageTokensPerSession": round(sum(record.token_count for record in records) / sessions, 2),
                "averageWordCountPerSession": round(sum(record.word_count for record in records) / sessions, 2),
            })

        return {"dimension": filters.dimension, "metric": filters.metric, "items": items}

    def model_comparison(self, filters: DashboardFilters) -> list[dict]:
        usage = self._filter_usage(filters, require_data=True)
        findings = self._filter_findings(filters)
        by_model: dict[str, list[UsageRecord]] = defaultdict(list)
        for record in usage:
            by_model[record.model_name].append(record)

        output = []
        for model_name, records in sorted(by_model.items(), key=lambda item: -sum(record.cost for record in item[1])):
            family = _family(model_name)
            family_findings = [finding for finding in findings if finding.model == family]
            sessions = len(records) or 1
            tokens = sum(record.token_count for record in records) or 1
            findings_count = sum(1 for finding in family_findings if finding.type in {"secret", "pii", "slopsquat"})
            output.append({
                "model": model_name,
                "provider": family,
                "usage": {"events": len(records), "tokens": sum(record.token_count for record in records), "sessions": sessions},
                "costs": {"total": round(sum(record.cost for record in records), 4), "perToken": round(sum(record.cost for record in records) / tokens, 6), "perSession": round(sum(record.cost for record in records) / sessions, 4)},
                "risk": {"leakCount": findings_count, "leakRate": round((findings_count / sessions) * 1000, 2), "hallucRate": round((sum(1 for finding in family_findings if finding.type == "slopsquat") / sessions) * 1000, 2)},
                "costPerQualityRatio": round(sum(record.cost for record in records) / (1 + findings_count), 4),
            })
        return output

    def findings(self, filters: DashboardFilters) -> dict:
        findings = self._filter_findings(filters)
        findings.sort(key=lambda record: record.timestamp, reverse=True)
        page = findings[filters.offset : filters.offset + filters.limit]
        return {"items": [self._finding_payload(finding) for finding in page], "total": len(findings), "offset": filters.offset, "limit": filters.limit}

    def finding_detail(self, finding_id: str) -> dict | None:
        for finding in self._repository.list_findings():
            if finding.id == finding_id:
                payload = self._finding_payload(finding)
                payload.update({"fullContext": finding.match_context, "remediationHistory": [], "relatedFindings": [], "duplicateCount": 1})
                return payload
        return None

    def update_finding_status(self, finding_id: str, status: str, notes: str | None = None) -> dict | None:
        finding = self._repository.update_finding_status(finding_id, status, notes)
        return self._finding_payload(finding) if finding else None

    def severity_distribution(self, filters: DashboardFilters) -> dict:
        findings = self._filter_findings(filters)
        output: dict[str, dict[str, int]] = {"secrets": {"critical": 0, "high": 0, "medium": 0}, "pii": {"critical": 0, "high": 0, "medium": 0}, "slopsquat": {"critical": 0, "high": 0, "medium": 0}}
        for finding in findings:
            output[{"secret": "secrets", "pii": "pii", "slopsquat": "slopsquat"}[finding.type]][finding.severity] += 1
        return output

    def leak_counts(self, filters: DashboardFilters) -> list[dict]:
        findings = [finding for finding in self._filter_findings(filters) if finding.type in {"secret", "pii", "slopsquat"}]
        grouped: dict[tuple[str, str], int] = defaultdict(int)
        for finding in findings:
            if filters.model and finding.model != filters.model.lower() and finding.provider != filters.model.lower():
                continue
            if filters.category and finding.type != filters.category:
                continue
            grouped[(finding.model, finding.type)] += 1
        return [{"model": model, "category": category, "leakCount": count} for (model, category), count in sorted(grouped.items(), key=lambda item: (-item[1], item[0][0], item[0][1]))]

    def slopsquatting(self, filters: DashboardFilters) -> list[dict]:
        findings = [finding for finding in self._filter_findings(filters) if finding.type == "slopsquat"]
        by_bucket: dict[str, list[FindingRecord]] = defaultdict(list)
        for finding in findings:
            if filters.dimension == "department":
                group_key = finding.department or "unknown"
            elif filters.dimension == "provider":
                group_key = finding.provider
            else:
                group_key = finding.model
            by_bucket[group_key].append(finding)

        usage_total = max(1, len(self._filter_usage(filters)))
        output = []
        for key, bucket in sorted(by_bucket.items(), key=lambda item: -len(item[1])):
            output.append({
                "provider": key,
                "hallucCount": len(bucket),
                "hallucRate": round(float(len(bucket)) * 1000 / usage_total, 2),
                "fabricationTypes": {
                    "packages": sum(1 for finding in bucket if any(token in finding.match_value.lower() for token in ["pip", "npm", "package", "install"])),
                    "endpoints": sum(1 for finding in bucket if "http" in finding.match_value.lower() or "endpoint" in finding.match_value.lower()),
                    "cliTools": sum(1 for finding in bucket if "cmd" in finding.match_value.lower() or "cli" in finding.match_value.lower()),
                    "rbacRoles": sum(1 for finding in bucket if "role" in finding.match_value.lower() or "scope" in finding.match_value.lower()),
                },
            })
        return output

    def duplicate_secrets(self, filters: DashboardFilters) -> list[dict]:
        findings = [finding for finding in self._filter_findings(filters) if finding.type == "secret"]
        grouped: dict[str, list[FindingRecord]] = defaultdict(list)
        for finding in findings:
            grouped[hashlib.sha256(finding.match_value.encode("utf-8", errors="ignore")).hexdigest()].append(finding)

        output = []
        for secret_hash, bucket in grouped.items():
            if len({finding.provider for finding in bucket}) < 2:
                continue
            output.append({
                "secretHash": secret_hash,
                "category": bucket[0].category,
                "firstDetected": min(finding.timestamp for finding in bucket),
                "lastDetected": max(finding.timestamp for finding in bucket),
                "affectedUsers": len({finding.conversation_id for finding in bucket}),
                "affectedSessions": len({finding.message_id for finding in bucket}),
                "departments": sorted({finding.department for finding in bucket if finding.department}),
                "severity": "critical",
            })
        return sorted(output, key=lambda item: (-item["affectedUsers"], item["firstDetected"]))

    def time_series(self, filters: DashboardFilters) -> dict:
        usage = self._filter_usage(filters)
        findings = self._filter_findings(filters)
        metric = filters.metric
        bucketed: dict[str, float] = defaultdict(float)
        if metric == "findings":
            for finding in findings:
                bucketed[finding.timestamp.strftime("%Y-%m-%d")] += 1
        else:
            for record in usage:
                key = record.usage_start.strftime("%Y-%m-%d")
                if metric == "cost":
                    bucketed[key] += record.cost
                elif metric == "events":
                    bucketed[key] += 1
                elif metric == "tokens":
                    bucketed[key] += record.token_count
        return {"metric": metric, "granularity": filters.dimension if filters.dimension in {"hour", "day", "week"} else "day", "data": [{"timestamp": key, "value": round(value, 2)} for key, value in sorted(bucketed.items())]}

    def anomalies(self, filters: DashboardFilters) -> list[dict]:
        usage = self._filter_usage(filters)
        buckets: dict[str, list[UsageRecord]] = defaultdict(list)
        for record in usage:
            buckets[record.department_id].append(record)

        alerts = []
        for department, records in buckets.items():
            daily = defaultdict(float)
            for record in records:
                daily[record.usage_start.strftime("%Y-%m-%d")] += record.cost
            values = list(daily.values())
            if len(values) < 2:
                continue
            average = mean(values)
            deviation = pstdev(values) or 1
            observed = values[-1]
            z_score = (observed - average) / deviation
            if abs(z_score) >= 2:
                alerts.append({"department": department, "period": list(daily.keys())[-1], "metric": "cost", "baselineValue": round(average, 4), "observedValue": round(observed, 4), "zScore": round(z_score, 2), "severity": "high" if z_score > 0 else "low", "explanation": f"{department} cost deviated from baseline"})
        return alerts

    def patterns_by_time(self, filters: DashboardFilters) -> dict:
        findings = self._filter_findings(filters)
        hourly = defaultdict(lambda: {"leakCount": 0, "criticalCount": 0})
        daily = defaultdict(lambda: {"leakCount": 0})
        for finding in findings:
            hour = finding.timestamp.hour
            weekday = finding.timestamp.strftime("%A")
            hourly[hour]["leakCount"] += 1
            daily[weekday]["leakCount"] += 1
            if finding.severity == "critical":
                hourly[hour]["criticalCount"] += 1
        return {"hourly": [{"hour": hour, **values} for hour, values in sorted(hourly.items())], "daily": [{"dayOfWeek": day, **values} for day, values in daily.items()]}

    def complexity_scatter(self, filters: DashboardFilters) -> list[dict]:
        usage = self._filter_usage(filters)
        findings = self._filter_findings(filters)
        counts_by_model = Counter(finding.model for finding in findings if finding.type in {"secret", "pii", "slopsquat"})
        output = []
        for record in usage:
            provider = _family(record.model_name)
            if filters.provider and provider != filters.provider.lower():
                continue
            output.append({
                "conversationId": record.id,
                "tokenCount": record.token_count,
                "findingCount": counts_by_model.get(provider, 0),
                "provider": provider,
                "cost": round(record.cost, 4),
                "department": record.department_id,
                "severity": "critical" if counts_by_model.get(provider, 0) > 0 else "medium",
            })
        return output

    def alerts(self, filters: DashboardFilters) -> list[dict]:
        findings = self._filter_findings(filters)
        findings.sort(key=lambda record: record.timestamp, reverse=True)
        return [self._alert_payload(finding) for finding in findings[: filters.limit]]

    def acknowledge_alert(self, finding_id: str, notes: str | None = None) -> dict | None:
        finding = self._repository.update_finding_status(finding_id, "acknowledged", notes)
        return self._alert_payload(finding) if finding else None

    def _finding_payload(self, finding: FindingRecord) -> dict:
        return {
            "id": finding.id,
            "type": finding.type,
            "severity": finding.severity,
            "category": finding.category,
            "model": finding.model,
            "provider": finding.provider,
            "conversationId": finding.conversation_id,
            "messageId": finding.message_id,
            "role": finding.role,
            "detectedAt": finding.timestamp,
            "matchValue": finding.match_value,
            "contextPreview": finding.match_context,
            "status": finding.status,
            "department": finding.department,
            "confidence": finding.confidence,
        }

    def _alert_payload(self, finding: FindingRecord) -> dict:
        return {
            "id": finding.id,
            "type": finding.type,
            "severity": finding.severity,
            "title": f"{finding.type.title()} finding",
            "message": finding.match_context,
            "timestamp": finding.timestamp,
            "department": finding.department or "unknown",
            "provider": finding.provider,
            "conversationId": finding.conversation_id,
            "status": finding.status,
            "actionUrl": f"/dashboard/findings/{finding.id}",
        }


default_dashboard_service = DashboardService()


# Database-backed dashboard service using materialized views
# This service queries from mv_deterministic_* views for fast dashboard responses

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class DatabaseDashboardService:
    """Dashboard service backed by materialized views for fast queries.
    
    This service reads from pre-computed materialized views:
    - mv_deterministic_overview
    - mv_deterministic_conversations
    - mv_deterministic_top_matches
    - mv_deterministic_by_department
    - mv_deterministic_timeline
    """

    def __init__(self, session_factory=async_session_factory):
        self._session_factory = session_factory

    async def get_overview(self, department: str | None = None) -> dict:
        """Get overview stats from materialized view."""
        async with self._session_factory() as session:
            repository = DeterministicAnalysisRepository(session)
            stats = await repository.get_overview_stats()
            
            if not stats:
                return {
                    "totalMatches": 0,
                    "affectedConversations": 0,
                    "criticalMatches": 0,
                    "highMatches": 0,
                    "mediumMatches": 0,
                    "piiMatches": 0,
                    "secretMatches": 0,
                    "lastAnalysisRun": None,
                }
            
            return {
                "totalMatches": stats.get("total_matches", 0),
                "affectedConversations": stats.get("affected_conversations", 0),
                "totalProviders": stats.get("total_providers", 0),
                "criticalMatches": stats.get("critical_matches", 0),
                "highMatches": stats.get("high_matches", 0),
                "mediumMatches": stats.get("medium_matches", 0),
                "lowMatches": stats.get("low_matches", 0),
                "piiMatches": stats.get("pii_matches", 0),
                "secretMatches": stats.get("secret_matches", 0),
                "financialMatches": stats.get("financial_matches", 0),
                "lastAnalysisRun": stats.get("last_analysis_run"),
                "refreshedAt": stats.get("refreshed_at"),
            }

    async def get_findings_from_view(
        self,
        department: str | None = None,
        severity: str | None = None,
        category: str | None = None,
        provider: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict:
        """Get findings from materialized view (fast)."""
        async with self._session_factory() as session:
            repository = DeterministicAnalysisRepository(session)
            
            # Use top matches view for critical/high, conversations view for others
            if severity in ("critical", "high", None):
                items = await repository.get_top_matches_from_view(
                    department=department,
                    severity=severity,
                    limit=limit + offset,
                )
            else:
                # For medium/low, get from conversations
                conversations = await repository.get_conversations_from_view(
                    department=department,
                    provider=provider,
                    severity=severity,
                    limit=limit,
                    offset=offset,
                )
                items = self._conversations_to_findings(conversations)
            
            return {
                "items": items[offset:offset + limit],
                "total": len(items),  # Note: actual count may be higher
                "offset": offset,
                "limit": limit,
            }

    async def get_conversations(
        self,
        department: str | None = None,
        provider: str | None = None,
        severity: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict:
        """Get conversation summaries from materialized view."""
        async with self._session_factory() as session:
            repository = DeterministicAnalysisRepository(session)
            items = await repository.get_conversations_from_view(
                department=department,
                provider=provider,
                severity=severity,
                limit=limit,
                offset=offset,
            )
            
            return {
                "items": items,
                "total": len(items),  # Note: may need separate count query
                "offset": offset,
                "limit": limit,
            }

    async def get_department_stats(self) -> list[dict]:
        """Get department statistics from materialized view."""
        async with self._session_factory() as session:
            repository = DeterministicAnalysisRepository(session)
            return await repository.get_department_stats_from_view()

    async def get_timeline(
        self,
        days: int = 30,
        category: str | None = None,
    ) -> list[dict]:
        """Get timeline data from materialized view."""
        async with self._session_factory() as session:
            repository = DeterministicAnalysisRepository(session)
            return await repository.get_timeline_from_view(days=days, category=category)

    async def get_severity_distribution(
        self,
        department: str | None = None,
    ) -> dict:
        """Get severity distribution from materialized view."""
        async with self._session_factory() as session:
            repository = DeterministicAnalysisRepository(session)
            stats = await repository.get_overview_stats()
            
            if not stats:
                return {"critical": 0, "high": 0, "medium": 0, "low": 0}
            
            return {
                "critical": stats.get("critical_matches", 0),
                "high": stats.get("high_matches", 0),
                "medium": stats.get("medium_matches", 0),
                "low": stats.get("low_matches", 0),
            }

    def _conversations_to_findings(self, conversations: list[dict]) -> list[dict]:
        """Convert conversation summary to finding format."""
        findings = []
        for conv in conversations:
            finding = {
                "id": f"{conv.get('conversation_key')}:summary",
                "type": "secret" if conv.get("secret_count", 0) > 0 else "pii",
                "severity": conv.get("highest_severity", "medium"),
                "category": conv.get("labels", ["secret"])[0] if conv.get("labels") else "secret",
                "model": conv.get("model_name", "unknown"),
                "provider": conv.get("provider", "unknown"),
                "conversationId": conv.get("conversation_key"),
                "matchCount": conv.get("match_count", 0),
                "secretCount": conv.get("secret_count", 0),
                "piiCount": conv.get("pii_count", 0),
                "department": conv.get("department"),
                "conversationTitle": conv.get("conversation_title"),
                "timestamp": conv.get("last_match_at"),
            }
            findings.append(finding)
        return findings


# Singleton instance
default_db_dashboard_service = DatabaseDashboardService()
