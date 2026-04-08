from __future__ import annotations

import hashlib
import json
import re
from dataclasses import replace
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.config import settings
from app.domain.dashboard import ConversationMessage, ConversationRecord, FindingRecord, UsageRecord


SECRET_PATTERNS: dict[str, tuple[re.Pattern[str], str]] = {
    "api_key": (re.compile(r"\b(?:sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{20,})\b"), "high"),
    "access_token": (re.compile(r"\b(?:eyJ[a-zA-Z0-9_-]{20,}|xox[baprs]-[A-Za-z0-9-]{10,})\b"), "high"),
    "password": (re.compile(r"(?i)\bpassword\b\s*[:=]\s*['\"]?([^\s'\"]{6,})"), "high"),
    "private_key": (re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----"), "critical"),
    "connection_string": (re.compile(r"\b(?:postgres|mysql|mssql|mongodb)://\S+", re.IGNORECASE), "critical"),
    "webhook_url": (re.compile(r"https?://hooks\.[^\s]+", re.IGNORECASE), "medium"),
    "client_secret": (re.compile(r"(?i)\bclient[_-]?secret\b\s*[:=]\s*['\"]?([^\s'\"]{6,})"), "critical"),
    "tenant_id": (re.compile(r"(?i)\btenant[_-]?id\b\s*[:=]\s*['\"]?([0-9a-f-]{16,})"), "medium"),
}


def _project_root() -> Path:
    return Path(__file__).resolve().parents[5]


def _parse_timestamp(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str):
        try:
            normalized = value.replace("Z", "+00:00")
            parsed = datetime.fromisoformat(normalized)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return None


def _normalize_text(value: Any) -> str:
    if isinstance(value, str):
        return value.replace("\x00", "")
    if isinstance(value, list):
        parts = []
        for block in value:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                for key in ("text", "content", "message", "prompt"):
                    if isinstance(block.get(key), str):
                        parts.append(block[key])
                        break
        return "\n".join(parts)
    if isinstance(value, dict):
        for key in ("text", "content", "message", "prompt"):
            if isinstance(value.get(key), str):
                return value[key]
    return ""


def _message_author(message: dict[str, Any]) -> str:
    return str(message.get("author") or message.get("role") or message.get("speaker") or "unknown")


def _message_content(message: dict[str, Any]) -> str:
    content = message.get("content")
    if isinstance(content, str):
        return content.replace("\x00", "")
    if isinstance(content, list):
        return _normalize_text(content)
    if isinstance(content, dict):
        return _normalize_text(content)
    for key in ("text", "message", "prompt"):
        if isinstance(message.get(key), str):
            return str(message[key]).replace("\x00", "")
    return ""


def _conversation_messages(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        messages = payload.get("messages") or payload.get("conversation")
        if isinstance(messages, list):
            return [message for message in messages if isinstance(message, dict)]
        return []
    if isinstance(payload, list):
        return [message for message in payload if isinstance(message, dict)]
    return []


def _conversation_entries(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        return [payload]
    return []


def _extract_conversation_id(entry: dict[str, Any], fallback: str) -> str:
    return str(entry.get("conversation_hash") or entry.get("conversation_id") or entry.get("url") or fallback)


def _extract_provider(entry: dict[str, Any], fallback: str) -> str:
    return _normalize_family(str(entry.get("author") or entry.get("model") or entry.get("provider") or fallback))


def _extract_title(entry: dict[str, Any], fallback: str) -> str:
    return str(entry.get("title") or entry.get("name") or fallback)


def _extract_exported_at(entry: dict[str, Any]) -> datetime | None:
    return _parse_timestamp(entry.get("date") or entry.get("timestamp") or entry.get("created_at"))


def _word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text))


def _normalize_family(name: str | None) -> str:
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


def _hash_id(*parts: str) -> str:
    payload = "|".join(parts).encode("utf-8", errors="ignore")
    return hashlib.sha1(payload).hexdigest()[:16]


@lru_cache(maxsize=1)
def _load_usage_records(root: str) -> tuple[UsageRecord, ...]:
    path = Path(root) / "logs.jsonl"
    records: list[UsageRecord] = []
    if not path.exists():
        return tuple(records)

    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            purpose = str(payload.get("purpose") or "")
            tokens = int(payload.get("token_count") or 0)
            records.append(
                UsageRecord(
                    id=str(payload.get("id") or _hash_id(line)),
                    user_id_hash=str(payload.get("user_id_hash") or ""),
                    department_id=str(payload.get("department_id") or "unknown"),
                    tool_name=str(payload.get("tool_name") or "unknown"),
                    model_name=str(payload.get("model_name") or "unknown"),
                    usage_start=_parse_timestamp(payload.get("usage_start")) or datetime.now(timezone.utc),
                    usage_end=_parse_timestamp(payload.get("usage_end")) or datetime.now(timezone.utc),
                    token_count=tokens,
                    cost=float(payload.get("cost") or 0),
                    purpose=purpose,
                    region=str(payload.get("region") or "") or None,
                    word_count=max(_word_count(purpose), max(1, tokens // 4)),
                )
            )
    return tuple(records)


@lru_cache(maxsize=1)
def _load_conversations(root: str) -> tuple[ConversationRecord, ...]:
    exports_dir = Path(root) / "chat-exports"
    records: list[ConversationRecord] = []
    if not exports_dir.exists():
        return tuple(records)

    for path in sorted(exports_dir.glob("*.json")):
        with path.open(encoding="utf-8") as handle:
            payload = json.load(handle)

        for entry_index, entry in enumerate(_conversation_entries(payload)):
            messages: list[ConversationMessage] = []
            for message_index, message in enumerate(_conversation_messages(entry)):
                content = _message_content(message)
                if not content:
                    continue
                messages.append(
                    ConversationMessage(
                        id=str(message.get("id") or message.get("turn_identifier") or _hash_id(path.stem, str(entry_index), str(message_index), content[:32])),
                        author=_message_author(message),
                        content=content,
                    )
                )

            if not messages:
                continue

            records.append(
                ConversationRecord(
                    conversation_id=_extract_conversation_id(entry, f"{path.stem}-{entry_index}"),
                    provider=_extract_provider(entry, path.stem.split("_")[0]),
                    title=_extract_title(entry, path.stem),
                    exported_at=_extract_exported_at(entry),
                    messages=tuple(messages),
                )
            )

    return tuple(records)




def _load_persisted_findings() -> tuple[FindingRecord, ...] | None:
    try:
        import psycopg2

        database_url = settings.database_url.replace("+asyncpg", "")
        if not database_url.startswith("postgres"):
            return None

        with psycopg2.connect(database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id FROM deterministic_analysis_runs
                    ORDER BY completed_at DESC
                    LIMIT 1
                    """
                )
                latest_run = cur.fetchone()
                if not latest_run:
                    return None

                cur.execute(
                    """
                    SELECT
                        id, department, source_file, conversation_key, conversation_title, provider,
                        model_name, message_id, message_timestamp, author, role, source_field,
                        company_rule_id, company_label, company_category, company_source_table,
                        company_source_field, matched_text, match_context, severity, confidence
                    FROM deterministic_chat_matches
                    WHERE analysis_run_id = %s
                    ORDER BY conversation_key, message_timestamp NULLS LAST, message_id
                    """,
                    (latest_run[0],),
                )
                rows = cur.fetchall()
    except Exception:
        return None

    if not rows:
        return None

    findings: list[FindingRecord] = []
    for row in rows:
        finding_type = "pii" if row[14] == "pii" else "secret"
        provider = _normalize_family(row[5])
        model_name = _normalize_family(row[6] or row[5])
        findings.append(
            FindingRecord(
                id=row[0],
                type=finding_type,
                severity=row[19],
                category=row[14],
                model=model_name,
                provider=provider,
                conversation_id=row[3],
                message_id=row[7],
                role=row[10],
                timestamp=row[8] or datetime.now(timezone.utc),
                match_value=row[17],
                match_context=row[18],
                source_field=row[11],
                confidence=float(row[20]),
                department=row[1],
                status="open",
                notes=None,
                extra={
                    "companyLabel": row[13],
                    "companyCategory": row[14],
                    "companySourceTable": row[15],
                    "companySourceField": row[16],
                },
            )
        )

    return tuple(findings)


class DashboardRepository:
    def __init__(self, root: Path | None = None):
        self._root = root or _project_root()
        self._status_overrides: dict[str, tuple[str, str | None]] = {}

    def list_usage_records(self) -> list[UsageRecord]:
        return list(_load_usage_records(str(self._root)))

    def list_conversations(self) -> list[ConversationRecord]:
        return list(_load_conversations(str(self._root)))

    def list_findings(self) -> list[FindingRecord]:
        persisted = _load_persisted_findings() or tuple()
        findings = [replace(finding) for finding in persisted]
        for finding in findings:
            if finding.id in self._status_overrides:
                finding.status, finding.notes = self._status_overrides[finding.id]
        return findings

    def update_finding_status(self, finding_id: str, status: str, notes: str | None = None) -> FindingRecord | None:
        for finding in self.list_findings():
            if finding.id == finding_id:
                self._status_overrides[finding_id] = (status, notes)
                updated = replace(finding)
                updated.status = status
                updated.notes = notes
                return updated
        return None


default_dashboard_repository = DashboardRepository()
