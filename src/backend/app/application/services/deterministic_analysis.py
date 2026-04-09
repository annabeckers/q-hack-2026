from __future__ import annotations

import asyncio
import hashlib
import json
import re
from collections import Counter, defaultdict

from app.application.config import get_deterministic_rules_config
from app.domain.analysis import ChatMessageRecord, CompanyReferenceRule, ConversationSummaryRecord, DeterministicMatchRecord
from app.infrastructure.database import async_session_factory
from app.infrastructure.repositories.deterministic_analysis_repository import DeterministicAnalysisRepository

# Config singleton for department inference
_rules_config = get_deterministic_rules_config()


def _normalize_text(value: str) -> str:
    return " ".join(value.split())


def _build_context(text: str, start: int, end: int, padding: int = 80) -> str:
    left = max(0, start - padding)
    right = min(len(text), end + padding)
    return text[left:right].strip()


def _stable_id(*parts: str) -> str:
    payload = "|".join(parts).encode("utf-8", errors="ignore")
    return hashlib.sha1(payload).hexdigest()[:20]


def _infer_department(text: str | None) -> str | None:
    """Infer department from keywords in text using configuration."""
    return _rules_config.infer_department(text)


class DeterministicAnalysisService:
    def __init__(self, session_factory=async_session_factory):
        self._session_factory = session_factory
        self._ensure_lock = asyncio.Lock()

    async def run(self) -> dict:
        async with self._session_factory() as session:
            repository = DeterministicAnalysisRepository(session)
            await repository.ensure_schema()

            rules = await repository.load_company_reference_rules()
            chats = await repository.load_chat_messages()

            matches = self._scan_messages(rules, chats)
            summaries = self._summarize(matches)

            run_id = await repository.save_analysis_run(
                source_message_count=len(chats),
                rule_count=len(rules),
                match_count=len(matches),
                status="completed",
            )

            await repository.save_matches([
                DeterministicMatchRecord(
                    id=match.id,
                    analysis_run_id=run_id,
                    department=match.department,
                    source_file=match.source_file,
                    conversation_key=match.conversation_key,
                    conversation_title=match.conversation_title,
                    provider=match.provider,
                    model_name=match.model_name,
                    message_id=match.message_id,
                    message_timestamp=match.message_timestamp,
                    author=match.author,
                    role=match.role,
                    source_field=match.source_field,
                    company_rule_id=match.company_rule_id,
                    company_label=match.company_label,
                    company_category=match.company_category,
                    company_source_table=match.company_source_table,
                    company_source_field=match.company_source_field,
                    matched_text=match.matched_text,
                    match_context=match.match_context,
                    severity=match.severity,
                    confidence=match.confidence,
                )
                for match in matches
            ])

            await repository.save_summaries(
                [
                    ConversationSummaryRecord(
                        analysis_run_id=run_id,
                        conversation_key=summary["conversation_key"],
                        department=summary["department"],
                        provider=summary["provider"],
                        model_name=summary["model_name"],
                        match_count=summary["match_count"],
                        secret_count=summary["secret_count"],
                        pii_count=summary["pii_count"],
                        financial_count=summary["financial_count"],
                        labels_json=json.dumps(summary["labels_json"], ensure_ascii=False),
                        highest_severity=summary["highest_severity"],
                    )
                    for summary in summaries
                ]
            )

            await session.commit()

            # Refresh materialized views for fast dashboard queries
            await repository.refresh_materialized_views()

            return {
                "analysis_run_id": run_id,
                "source_message_count": len(chats),
                "rule_count": len(rules),
                "match_count": len(matches),
                "conversation_count": len(summaries),
            }

    async def ensure_completed(self) -> dict | None:
        async with self._ensure_lock:
            async with self._session_factory() as session:
                repository = DeterministicAnalysisRepository(session)
                await repository.ensure_schema()
                if await repository.has_completed_analysis():
                    return None

            return await self.run()

    def _scan_messages(self, rules: list[CompanyReferenceRule], chats: list[ChatMessageRecord]) -> list[DeterministicMatchRecord]:
        compiled_rules = [
            (
                rule,
                re.compile(rule.pattern, re.IGNORECASE),
            )
            for rule in rules
            if rule.pattern
        ]
        matches: list[DeterministicMatchRecord] = []

        for chat in chats:
            text = _normalize_text(chat.source_text)
            if not text:
                continue
            for rule, pattern in compiled_rules:
                for match in pattern.finditer(text):
                    matched_text = match.group(0)
                    matches.append(
                        DeterministicMatchRecord(
                            id=_stable_id(chat.conversation_key, chat.message_id, rule.id, matched_text),
                            analysis_run_id="pending",
                            department=_infer_department(chat.conversation_title or chat.source_text),
                            source_file=chat.source_file,
                            conversation_key=chat.conversation_key,
                            conversation_title=chat.conversation_title,
                            provider=chat.provider,
                            model_name=chat.model_name,
                            message_id=chat.message_id,
                            message_timestamp=chat.message_timestamp,
                            author=chat.author,
                            role=chat.role,
                            source_field="user_text_clean",
                            company_rule_id=rule.id,
                            company_label=rule.label,
                            company_category=rule.category,
                            company_source_table=rule.source_table,
                            company_source_field=rule.source_field,
                            matched_text=matched_text,
                            match_context=_build_context(text, match.start(), match.end()),
                            severity=rule.severity,
                            confidence=1.0,
                        )
                    )

        return matches

    def _summarize(self, matches: list[DeterministicMatchRecord]) -> list[dict]:
        grouped: dict[str, list[DeterministicMatchRecord]] = defaultdict(list)
        for match in matches:
            grouped[match.conversation_key].append(match)

        summaries: list[dict] = []
        for conversation_key, items in grouped.items():
            categories = Counter(item.company_category for item in items)
            severity_order = {"critical": 3, "high": 2, "medium": 1, "low": 0}
            highest = max(items, key=lambda item: severity_order.get(item.severity, 0)).severity
            summaries.append(
                {
                    "conversation_key": conversation_key,
                    "department": items[0].department,
                    "provider": items[0].provider,
                    "model_name": items[0].model_name,
                    "match_count": len(items),
                    "secret_count": categories.get("secret", 0),
                    "pii_count": categories.get("pii", 0),
                    "financial_count": categories.get("financial", 0),
                    "labels_json": sorted({item.company_label for item in items}),
                    "highest_severity": highest,
                }
            )
        return summaries


default_deterministic_analysis_service = DeterministicAnalysisService()
