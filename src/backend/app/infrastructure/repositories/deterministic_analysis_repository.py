from __future__ import annotations

import json
import re
from dataclasses import asdict
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.analysis import ChatMessageRecord, CompanyReferenceRule, ConversationSummaryRecord, DeterministicMatchRecord
from app.domain.interfaces import AbstractDeterministicAnalysisRepository


RULE_FIELD_MAP: dict[str, dict[str, tuple[str, str]]] = {
    "costumers": {
        "company_name": ("pii", "high"),
        "contact_name": ("pii", "high"),
        "email": ("pii", "critical"),
        "costumer_code": ("secret", "high"),
        "segment": ("secret", "medium"),
        "annual_contract_value_eur": ("secret", "critical"),
    },
    "employees": {
        "employee_number": ("secret", "high"),
        "full_name": ("pii", "high"),
        "department": ("secret", "medium"),
        "job_title": ("secret", "medium"),
        "manager_name": ("pii", "high"),
    },
    "documents": {
        "title": ("secret", "medium"),
        "source": ("secret", "medium"),
        "source_type": ("secret", "low"),
        "content_preview": ("secret", "critical"),
        "metadata_json": ("secret", "medium"),
    },
}


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def _build_regex_pattern(value: str) -> str:
    normalized = " ".join(_stringify(value).split())
    if not normalized:
        return ""
    tokens = [token for token in re.findall(r"[A-Za-z0-9]+", normalized)]
    if len(tokens) > 1:
        pieces = [re.escape(token) for token in tokens]
        return r"\b" + r"[\s\-_./]*".join(pieces) + r"\b"
    if normalized.isdigit():
        if len(normalized) >= 4:
            return r"\b" + r"[\s,._-]*".join(list(normalized)) + r"\b"
        return rf"\b{normalized}\b"
    return rf"\b{re.escape(normalized)}\b"


def _extract_json_scalars(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except Exception:
        return [raw]

    values: list[str] = []

    def walk(node: Any) -> None:
        if node is None:
            return
        if isinstance(node, (str, int, float, bool)):
            values.append(_stringify(node))
            return
        if isinstance(node, dict):
            for key, value in node.items():
                values.append(_stringify(key))
                walk(value)
            return
        if isinstance(node, list):
            for item in node:
                walk(item)

    walk(parsed)
    return [value for value in values if value.strip()]


class DeterministicAnalysisRepository(AbstractDeterministicAnalysisRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def ensure_schema(self) -> None:
        statements = [
            """
            CREATE TABLE IF NOT EXISTS deterministic_analysis_runs (
                id TEXT PRIMARY KEY,
                source_message_count INTEGER NOT NULL,
                rule_count INTEGER NOT NULL,
                match_count INTEGER NOT NULL,
                status TEXT NOT NULL,
                notes TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                completed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS deterministic_company_rules (
                id TEXT PRIMARY KEY,
                source_table TEXT NOT NULL,
                source_record_id TEXT NOT NULL,
                source_field TEXT NOT NULL,
                label TEXT NOT NULL,
                category TEXT NOT NULL,
                severity TEXT NOT NULL,
                pattern TEXT NOT NULL,
                value TEXT NOT NULL,
                active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS deterministic_chat_matches (
                id TEXT PRIMARY KEY,
                analysis_run_id TEXT NOT NULL,
                department TEXT,
                source_file TEXT NOT NULL,
                conversation_key TEXT NOT NULL,
                conversation_title TEXT,
                provider TEXT NOT NULL,
                model_name TEXT,
                message_id TEXT NOT NULL,
                message_timestamp TIMESTAMPTZ,
                author TEXT NOT NULL,
                role TEXT NOT NULL,
                source_field TEXT NOT NULL,
                company_rule_id TEXT NOT NULL,
                company_label TEXT NOT NULL,
                company_category TEXT NOT NULL,
                company_source_table TEXT NOT NULL,
                company_source_field TEXT NOT NULL,
                matched_text TEXT NOT NULL,
                match_context TEXT NOT NULL,
                severity TEXT NOT NULL,
                confidence NUMERIC(4, 2) NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                UNIQUE (analysis_run_id, source_file, conversation_key, message_id, company_rule_id, matched_text)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS deterministic_conversation_summaries (
                analysis_run_id TEXT NOT NULL,
                conversation_key TEXT NOT NULL,
                department TEXT,
                provider TEXT NOT NULL,
                model_name TEXT,
                match_count INTEGER NOT NULL,
                secret_count INTEGER NOT NULL,
                pii_count INTEGER NOT NULL,
                financial_count INTEGER NOT NULL,
                labels_json TEXT NOT NULL,
                highest_severity TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (analysis_run_id, conversation_key)
            )
            """,
        ]
        for statement in statements:
            await self._session.execute(text(statement))

    async def has_completed_analysis(self) -> bool:
        result = await self._session.execute(
            text(
                """
                SELECT 1
                FROM deterministic_analysis_runs
                WHERE status = 'completed'
                ORDER BY completed_at DESC
                LIMIT 1
                """
            )
        )
        return result.first() is not None

    async def load_company_reference_rules(self) -> list[CompanyReferenceRule]:
        result = await self._session.execute(
            text(
                """
                SELECT id, source_table, source_record_id, source_field, label, category, severity, pattern, value
                FROM deterministic_company_rules
                ORDER BY source_table, label, source_field
                """
            )
        )
        rows = [CompanyReferenceRule(**row) for row in result.mappings().all()]
        if rows:
            return rows

        generated: list[CompanyReferenceRule] = []

        for table_name, field_map in RULE_FIELD_MAP.items():
            result = await self._session.execute(text(f"SELECT * FROM {table_name}"))
            source_rows = result.mappings().all()
            for row in source_rows:
                record_id = _stringify(row.get("id"))
                for field_name, (category, severity) in field_map.items():
                    raw_value = row.get(field_name)
                    if raw_value in (None, ""):
                        continue
                    if field_name == "metadata_json":
                        for idx, scalar in enumerate(_extract_json_scalars(_stringify(raw_value))):
                            pattern = _build_regex_pattern(scalar)
                            if not pattern:
                                continue
                            generated.append(
                                CompanyReferenceRule(
                                    id=f"{table_name}:{record_id}:{field_name}:{idx}",
                                    source_table=table_name,
                                    source_record_id=record_id,
                                    source_field=field_name,
                                    label=f"{table_name}.{field_name}[{idx}]",
                                    category=category,
                                    severity=severity,
                                    pattern=pattern,
                                    value=scalar,
                                )
                            )
                        continue

                    pattern = _build_regex_pattern(_stringify(raw_value))
                    if not pattern:
                        continue

                    generated.append(
                        CompanyReferenceRule(
                            id=f"{table_name}:{record_id}:{field_name}",
                            source_table=table_name,
                            source_record_id=record_id,
                            source_field=field_name,
                            label=f"{table_name}.{field_name}",
                            category=category,
                            severity=severity,
                            pattern=pattern,
                            value=_stringify(raw_value),
                        )
                    )

        await self.save_company_rules(generated)
        return generated

    async def load_chat_messages(self) -> list[ChatMessageRecord]:
        result = await self._session.execute(
            text(
                """
                SELECT source_file, conversation_key, conversation_title, provider, model_name,
                       message_id, message_timestamp, author, role, user_text_clean
                FROM chats
                ORDER BY conversation_timestamp NULLS LAST, message_index ASC
                """
            )
        )
        records: list[ChatMessageRecord] = []
        for row in result.mappings().all():
            records.append(
                ChatMessageRecord(
                    source_file=_stringify(row["source_file"]),
                    conversation_key=_stringify(row["conversation_key"]),
                    conversation_title=row.get("conversation_title"),
                    provider=_stringify(row["provider"]),
                    model_name=row.get("model_name"),
                    message_id=_stringify(row["message_id"]),
                    message_timestamp=row.get("message_timestamp"),
                    author=_stringify(row.get("author") or "unknown"),
                    role=_stringify(row.get("role") or "user"),
                    source_text=_stringify(row.get("user_text_clean") or ""),
                )
            )
        return records

    async def save_analysis_run(self, source_message_count: int, rule_count: int, match_count: int, status: str) -> str:
        from uuid import uuid4

        run_id = uuid4().hex
        await self._session.execute(
            text(
                """
                INSERT INTO deterministic_analysis_runs (id, source_message_count, rule_count, match_count, status, notes, created_at, completed_at)
                VALUES (:id, :source_message_count, :rule_count, :match_count, :status, NULL, NOW(), NOW())
                """
            ),
            {
                "id": run_id,
                "source_message_count": source_message_count,
                "rule_count": rule_count,
                "match_count": match_count,
                "status": status,
            },
        )
        return run_id

    async def save_company_rules(self, rules: list[CompanyReferenceRule]) -> None:
        for rule in rules:
            await self._session.execute(
                text(
                    """
                    INSERT INTO deterministic_company_rules (
                        id, source_table, source_record_id, source_field, label,
                        category, severity, pattern, value, active, created_at
                    ) VALUES (
                        :id, :source_table, :source_record_id, :source_field, :label,
                        :category, :severity, :pattern, :value, TRUE, NOW()
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        source_table = EXCLUDED.source_table,
                        source_record_id = EXCLUDED.source_record_id,
                        source_field = EXCLUDED.source_field,
                        label = EXCLUDED.label,
                        category = EXCLUDED.category,
                        severity = EXCLUDED.severity,
                        pattern = EXCLUDED.pattern,
                        value = EXCLUDED.value,
                        active = EXCLUDED.active
                    """
                ),
                asdict(rule),
            )

    async def save_matches(self, matches: list[DeterministicMatchRecord]) -> None:
        for match in matches:
            await self._session.execute(
                text(
                    """
                    INSERT INTO deterministic_chat_matches (
                        id, analysis_run_id, department, source_file, conversation_key, conversation_title,
                        provider, model_name, message_id, message_timestamp, author, role,
                        source_field, company_rule_id, company_label, company_category,
                        company_source_table, company_source_field, matched_text, match_context,
                        severity, confidence, created_at
                    ) VALUES (
                        :id, :analysis_run_id, :department, :source_file, :conversation_key, :conversation_title,
                        :provider, :model_name, :message_id, :message_timestamp, :author, :role,
                        :source_field, :company_rule_id, :company_label, :company_category,
                        :company_source_table, :company_source_field, :matched_text, :match_context,
                        :severity, :confidence, NOW()
                    )
                    ON CONFLICT (analysis_run_id, source_file, conversation_key, message_id, company_rule_id, matched_text)
                    DO UPDATE SET
                        conversation_title = EXCLUDED.conversation_title,
                        provider = EXCLUDED.provider,
                        model_name = EXCLUDED.model_name,
                        message_timestamp = EXCLUDED.message_timestamp,
                        author = EXCLUDED.author,
                        role = EXCLUDED.role,
                        source_field = EXCLUDED.source_field,
                        company_label = EXCLUDED.company_label,
                        company_category = EXCLUDED.company_category,
                        company_source_table = EXCLUDED.company_source_table,
                        company_source_field = EXCLUDED.company_source_field,
                        match_context = EXCLUDED.match_context,
                        severity = EXCLUDED.severity,
                        confidence = EXCLUDED.confidence
                    """
                ),
                asdict(match),
            )

    async def save_summaries(self, summaries: list[ConversationSummaryRecord]) -> None:
        for summary in summaries:
            await self._session.execute(
                text(
                    """
                    INSERT INTO deterministic_conversation_summaries (
                        analysis_run_id, conversation_key, department, provider, model_name, match_count,
                        secret_count, pii_count, financial_count, labels_json, highest_severity, created_at
                    ) VALUES (
                        :analysis_run_id, :conversation_key, :department, :provider, :model_name, :match_count,
                        :secret_count, :pii_count, :financial_count, :labels_json, :highest_severity, NOW()
                    )
                    ON CONFLICT (analysis_run_id, conversation_key) DO UPDATE SET
                        department = EXCLUDED.department,
                        provider = EXCLUDED.provider,
                        model_name = EXCLUDED.model_name,
                        match_count = EXCLUDED.match_count,
                        secret_count = EXCLUDED.secret_count,
                        pii_count = EXCLUDED.pii_count,
                        financial_count = EXCLUDED.financial_count,
                        labels_json = EXCLUDED.labels_json,
                        highest_severity = EXCLUDED.highest_severity
                    """
                ),
                asdict(summary),
            )
