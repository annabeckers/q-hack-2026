from __future__ import annotations

import json
import logging
import re
from dataclasses import asdict
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.config import get_deterministic_rules_config
from app.domain.analysis import ChatMessageRecord, CompanyReferenceRule, ConversationSummaryRecord, DeterministicMatchRecord
from app.domain.interfaces import AbstractDeterministicAnalysisRepository

logger = logging.getLogger(__name__)


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
            # Chats table (source data for analysis)
            """
            CREATE TABLE IF NOT EXISTS chats (
                id BIGSERIAL PRIMARY KEY,
                source_file TEXT NOT NULL,
                source_format VARCHAR(20),
                provider VARCHAR(50) NOT NULL,
                conversation_key TEXT NOT NULL,
                conversation_title TEXT,
                conversation_slug TEXT,
                export_author VARCHAR(50),
                model_name VARCHAR(100),
                conversation_timestamp TIMESTAMPTZ,
                message_id TEXT NOT NULL,
                parent_message_id TEXT,
                message_index INTEGER,
                message_timestamp TIMESTAMPTZ,
                author VARCHAR(20) NOT NULL,
                role VARCHAR(20) NOT NULL,
                language VARCHAR(50),
                user_text TEXT,
                user_text_clean TEXT,
                user_text_hash CHAR(64),
                metadata JSONB,
                UNIQUE (source_file, conversation_key, message_id)
            )
            """,
            """
            CREATE INDEX IF NOT EXISTS ix_chats_conversation_key ON chats (conversation_key)
            """,
            """
            CREATE INDEX IF NOT EXISTS ix_chats_provider ON chats (provider)
            """,
            """
            CREATE INDEX IF NOT EXISTS ix_chats_conversation_timestamp ON chats (conversation_timestamp)
            """,
            # Deterministic analysis tables
            """
            CREATE TABLE IF NOT EXISTS deterministic_analysis_runs (
                id TEXT PRIMARY KEY,
                source_message_count INTEGER NOT NULL,
                rule_count INTEGER NOT NULL,
                match_count INTEGER NOT NULL,
                status TEXT NOT NULL,
                notes TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
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
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
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
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
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
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
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
        # Try to load cached rules first
        try:
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
        except SQLAlchemyError as e:
            # Table may not exist yet (first run) - log and continue to generate
            logger.debug("Could not load cached rules, will generate from source tables: %s", e)

        generated: list[CompanyReferenceRule] = []
        config = get_deterministic_rules_config()

        # Iterate over configured tables and their fields from YAML config
        for table_name, table_fields in config.severity_rules.by_table_field.items():
            try:
                result = await self._session.execute(text(f"SELECT * FROM {table_name}"))  # noqa: S608
                source_rows = result.mappings().all()
            except SQLAlchemyError as e:
                # Source table may not exist yet - log warning and skip
                logger.warning("Could not load rules from table '%s': %s", table_name, e)
                continue

            for row in source_rows:
                record_id = _stringify(row.get("id"))
                for field_name, base_severity in table_fields.items():
                    raw_value = row.get(field_name)
                    if raw_value in (None, ""):
                        continue

                    # Resolve category and severity from config
                    category = config.category_rules.resolve(table_name, field_name)
                    severity = config.severity_rules.resolve(table_name, field_name, base_severity)

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
        try:
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
        except SQLAlchemyError as e:
            logger.error("Failed to load chat messages: %s", e)
            raise
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
                VALUES (:id, :source_message_count, :rule_count, :match_count, :status, NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
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
                        :category, :severity, :pattern, :value, TRUE, CURRENT_TIMESTAMP
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
                        :severity, :confidence, CURRENT_TIMESTAMP
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
                        :secret_count, :pii_count, :financial_count, :labels_json, :highest_severity, CURRENT_TIMESTAMP
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

    async def refresh_materialized_views(self) -> None:
        """Refresh all materialized views for deterministic analysis.
        
        Call this after saving matches to update dashboard views.
        Uses CONCURRENTLY to avoid locking.
        
        Note: This is a no-op for SQLite as it doesn't support materialized views.
        """
        # Check if we're using PostgreSQL (materialized views only work in PostgreSQL)
        dialect = self._session.bind.dialect.name if self._session.bind else ""
        if dialect != "postgresql":
            logger.debug("Skipping materialized view refresh for %s", dialect)
            return
        
        try:
            await self._session.execute(text("SELECT refresh_deterministic_views()"))
            logger.info("Refreshed deterministic analysis materialized views")
        except SQLAlchemyError as e:
            logger.error("Failed to refresh materialized views: %s", e)
            raise

    # Materialized View Query Methods (for dashboard)

    async def get_overview_stats(self) -> dict[str, Any] | None:
        """Get overview stats from materialized view (or base tables for SQLite)."""
        dialect = self._session.bind.dialect.name if self._session.bind else ""
        
        if dialect == "postgresql":
            # Use materialized view for PostgreSQL
            result = await self._session.execute(
                text("SELECT * FROM mv_deterministic_overview LIMIT 1")
            )
            row = result.mappings().first()
            return dict(row) if row else None
        else:
            # Fallback: compute stats from base tables for SQLite
            return await self._compute_overview_stats()
    
    async def _compute_overview_stats(self) -> dict[str, Any] | None:
        """Compute overview stats directly from base tables (for SQLite)."""
        result = await self._session.execute(
            text("""
                SELECT 
                    COUNT(*) as total_matches,
                    COUNT(DISTINCT conversation_key) as affected_conversations,
                    COUNT(DISTINCT provider) as total_providers,
                    SUM(CASE WHEN severity = 'critical' THEN 1 ELSE 0 END) as critical_matches,
                    SUM(CASE WHEN severity = 'high' THEN 1 ELSE 0 END) as high_matches,
                    SUM(CASE WHEN severity = 'medium' THEN 1 ELSE 0 END) as medium_matches,
                    SUM(CASE WHEN severity = 'low' THEN 1 ELSE 0 END) as low_matches,
                    SUM(CASE WHEN company_category = 'pii' THEN 1 ELSE 0 END) as pii_matches,
                    SUM(CASE WHEN company_category = 'secret' THEN 1 ELSE 0 END) as secret_matches,
                    SUM(CASE WHEN company_category = 'financial' THEN 1 ELSE 0 END) as financial_matches,
                    MAX(created_at) as last_analysis_run,
                    datetime('now') as refreshed_at
                FROM deterministic_chat_matches
            """)
        )
        row = result.mappings().first()
        return dict(row) if row else None

    async def get_conversations_from_view(
        self, 
        department: str | None = None,
        provider: str | None = None,
        severity: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Get conversation summaries from materialized view (or base tables for SQLite)."""
        dialect = self._session.bind.dialect.name if self._session.bind else ""
        
        if dialect == "postgresql":
            return await self._get_conversations_from_matview(department, provider, severity, limit, offset)
        else:
            return await self._get_conversations_from_base(department, provider, severity, limit, offset)
    
    async def _get_conversations_from_matview(
        self, 
        department: str | None = None,
        provider: str | None = None,
        severity: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Get conversation summaries from materialized view (PostgreSQL)."""
        where_clauses = []
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        
        if department:
            where_clauses.append("department = :department")
            params["department"] = department
        if provider:
            where_clauses.append("provider = :provider")
            params["provider"] = provider
        if severity:
            where_clauses.append("highest_severity = :severity")
            params["severity"] = severity
            
        where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        result = await self._session.execute(
            text(f"""
                SELECT * FROM mv_deterministic_conversations
                {where_sql}
                ORDER BY match_count DESC
                LIMIT :limit OFFSET :offset
            """),  # noqa: S608
            params,
        )
        return [dict(row) for row in result.mappings().all()]
    
    async def _get_conversations_from_base(
        self, 
        department: str | None = None,
        provider: str | None = None,
        severity: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Get conversation summaries from base tables (SQLite)."""
        where_clauses = []
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        
        if department:
            where_clauses.append("department = :department")
            params["department"] = department
        if provider:
            where_clauses.append("provider = :provider")
            params["provider"] = provider
        if severity:
            # Map severity string to numeric value
            severity_filter_sql = """(
                SELECT MAX(CASE severity 
                    WHEN 'critical' THEN 3 
                    WHEN 'high' THEN 2 
                    WHEN 'medium' THEN 1 
                    ELSE 0 
                END) 
                FROM deterministic_chat_matches m2 
                WHERE m2.conversation_key = m.conversation_key
            ) = CASE :severity 
                WHEN 'critical' THEN 3 
                WHEN 'high' THEN 2 
                WHEN 'medium' THEN 1 
                ELSE 0 
            END"""
            where_clauses.append(severity_filter_sql)
            params["severity"] = severity
            
        where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        result = await self._session.execute(
            text(f"""
                SELECT 
                    conversation_key,
                    MAX(conversation_title) as conversation_title,
                    MAX(provider) as provider,
                    MAX(model_name) as model_name,
                    MAX(department) as department,
                    COUNT(*) as match_count,
                    SUM(CASE WHEN company_category = 'secret' THEN 1 ELSE 0 END) as secret_count,
                    SUM(CASE WHEN company_category = 'pii' THEN 1 ELSE 0 END) as pii_count,
                    SUM(CASE WHEN company_category = 'financial' THEN 1 ELSE 0 END) as financial_count,
                    MAX(CASE severity 
                        WHEN 'critical' THEN 3 
                        WHEN 'high' THEN 2 
                        WHEN 'medium' THEN 1 
                        ELSE 0 
                    END) as severity_order
                FROM deterministic_chat_matches m
                {where_sql}
                GROUP BY conversation_key
                ORDER BY match_count DESC
                LIMIT :limit OFFSET :offset
            """),  # noqa: S608
            params,
        )
        rows = result.mappings().all()
        # Convert severity_order back to string
        result_list = []
        for row in rows:
            row_dict = dict(row)
            severity_map = {3: 'critical', 2: 'high', 1: 'medium', 0: 'low'}
            row_dict['highest_severity'] = severity_map.get(row_dict.pop('severity_order', 0), 'low')
            result_list.append(row_dict)
        return result_list

    async def get_top_matches_from_view(
        self,
        department: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get top matches (critical/high) from materialized view (or base tables for SQLite)."""
        dialect = self._session.bind.dialect.name if self._session.bind else ""
        
        if dialect == "postgresql":
            return await self._get_top_matches_from_matview(department, severity, limit)
        else:
            return await self._get_top_matches_from_base(department, severity, limit)
    
    async def _get_top_matches_from_matview(
        self,
        department: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get top matches from materialized view (PostgreSQL)."""
        where_clauses = []
        params: dict[str, Any] = {"limit": limit}
        
        if department:
            where_clauses.append("department = :department")
            params["department"] = department
        if severity:
            where_clauses.append("severity = :severity")
            params["severity"] = severity
            
        where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        result = await self._session.execute(
            text(f"""
                SELECT * FROM mv_deterministic_top_matches
                {where_sql}
                ORDER BY severity DESC, created_at DESC
                LIMIT :limit
            """),  # noqa: S608
            params,
        )
        return [dict(row) for row in result.mappings().all()]
    
    async def _get_top_matches_from_base(
        self,
        department: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get top matches from base tables (SQLite)."""
        where_clauses = ["severity IN ('critical', 'high')"]
        params: dict[str, Any] = {"limit": limit}
        
        if department:
            where_clauses.append("department = :department")
            params["department"] = department
        if severity:
            where_clauses.append("severity = :severity")
            params["severity"] = severity
            
        where_sql = "WHERE " + " AND ".join(where_clauses)
        
        result = await self._session.execute(
            text(f"""
                SELECT 
                    id,
                    department,
                    source_file,
                    conversation_key,
                    conversation_title,
                    provider,
                    model_name,
                    message_id,
                    message_timestamp,
                    author,
                    role,
                    company_label,
                    company_category as category,
                    company_source_table,
                    company_source_field,
                    matched_text,
                    match_context,
                    severity,
                    confidence,
                    created_at,
                    created_at as analysis_run_at
                FROM deterministic_chat_matches
                {where_sql}
                ORDER BY 
                    CASE severity 
                        WHEN 'critical' THEN 3 
                        WHEN 'high' THEN 2 
                        WHEN 'medium' THEN 1 
                        ELSE 0 
                    END DESC,
                    created_at DESC
                LIMIT :limit
            """),  # noqa: S608
            params,
        )
        return [dict(row) for row in result.mappings().all()]

    async def get_timeline_from_view(
        self,
        days: int = 30,
        category: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get timeline data from materialized view (or base tables for SQLite)."""
        dialect = self._session.bind.dialect.name if self._session.bind else ""
        
        if dialect == "postgresql":
            return await self._get_timeline_from_matview(days, category)
        else:
            return await self._get_timeline_from_base(days, category)
    
    async def _get_timeline_from_matview(
        self,
        days: int = 30,
        category: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get timeline data from materialized view (PostgreSQL)."""
        params: dict[str, Any] = {"days": days}
        where_clauses = ["day >= CURRENT_DATE - :days"]
        
        if category:
            where_clauses.append("category = :category")
            params["category"] = category
            
        result = await self._session.execute(
            text(f"""
                SELECT day, category, severity, provider, match_count, conversation_count
                FROM mv_deterministic_timeline
                WHERE {' AND '.join(where_clauses)}
                ORDER BY day DESC
            """),  # noqa: S608
            params,
        )
        return [dict(row) for row in result.mappings().all()]
    
    async def _get_timeline_from_base(
        self,
        days: int = 30,
        category: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get timeline data from base tables (SQLite)."""
        params: dict[str, Any] = {"days": days}
        where_clauses = ["message_timestamp >= datetime('now', '-' || :days || ' days')"]
        
        if category:
            where_clauses.append("company_category = :category")
            params["category"] = category
            
        where_sql = "WHERE " + " AND ".join(where_clauses)
            
        result = await self._session.execute(
            text(f"""
                SELECT 
                    date(message_timestamp) as day,
                    company_category as category,
                    severity,
                    provider,
                    COUNT(*) as match_count,
                    COUNT(DISTINCT conversation_key) as conversation_count
                FROM deterministic_chat_matches
                {where_sql}
                GROUP BY date(message_timestamp), company_category, severity, provider
                ORDER BY day DESC
            """),  # noqa: S608
            params,
        )
        return [dict(row) for row in result.mappings().all()]

    async def get_department_stats_from_view(self) -> list[dict[str, Any]]:
        """Get department statistics from materialized view (or base tables for SQLite)."""
        dialect = self._session.bind.dialect.name if self._session.bind else ""
        
        if dialect == "postgresql":
            result = await self._session.execute(
                text("SELECT * FROM mv_deterministic_by_department ORDER BY match_count DESC")
            )
        else:
            # SQLite fallback
            result = await self._session.execute(
                text("""
                    SELECT 
                        COALESCE(department, 'unknown') as department,
                        provider,
                        COUNT(*) as match_count,
                        COUNT(DISTINCT conversation_key) as conversation_count,
                        SUM(CASE WHEN severity = 'critical' THEN 1 ELSE 0 END) as critical_count,
                        SUM(CASE WHEN severity = 'high' THEN 1 ELSE 0 END) as high_count,
                        SUM(CASE WHEN company_category = 'pii' THEN 1 ELSE 0 END) as pii_count,
                        SUM(CASE WHEN company_category = 'secret' THEN 1 ELSE 0 END) as secret_count
                    FROM deterministic_chat_matches
                    GROUP BY COALESCE(department, 'unknown'), provider
                    ORDER BY match_count DESC
                """)
            )
        return [dict(row) for row in result.mappings().all()]

    async def get_rule_stats_from_view(self) -> list[dict[str, Any]]:
        """Get rule effectiveness statistics from materialized view (or base tables for SQLite)."""
        dialect = self._session.bind.dialect.name if self._session.bind else ""
        
        if dialect == "postgresql":
            result = await self._session.execute(
                text("SELECT * FROM mv_deterministic_rule_stats ORDER BY match_count DESC")
            )
        else:
            # SQLite fallback
            result = await self._session.execute(
                text("""
                    SELECT 
                        dcr.id as rule_id,
                        dcr.source_table,
                        dcr.source_field,
                        dcr.label,
                        dcr.category as rule_category,
                        dcr.severity as rule_severity,
                        COUNT(dcm.id) as match_count,
                        COUNT(DISTINCT dcm.conversation_key) as affected_conversations,
                        MAX(dcm.created_at) as last_match_at
                    FROM deterministic_company_rules dcr
                    LEFT JOIN deterministic_chat_matches dcm ON dcm.company_rule_id = dcr.id
                    GROUP BY dcr.id, dcr.source_table, dcr.source_field, dcr.label, 
                             dcr.category, dcr.severity
                    ORDER BY match_count DESC
                """)
            )
        return [dict(row) for row in result.mappings().all()]
