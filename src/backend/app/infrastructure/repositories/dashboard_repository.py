from __future__ import annotations

import hashlib
import json
import re
from dataclasses import replace
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

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

PII_PATTERNS: dict[str, tuple[re.Pattern[str], str]] = {
    "email": (re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE), "high"),
    "ip_address": (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "high"),
    "phone_number": (re.compile(r"\b(?:\+?\d{1,3}[\s-]?)?(?:\d[\s-]?){7,14}\b"), "medium"),
    "internal_path": (re.compile(r"(?:[A-Za-z]:\\|/)[\w.\\/-]+"), "medium"),
    "internal_url": (re.compile(r"https?://[\w.-]+(?:/[^\s]*)?", re.IGNORECASE), "medium"),
}

SLOPSQUAT_PATTERNS = [
    re.compile(r"(?i)\b(?:pip|npm|yarn|pnpm|cargo|go|dotnet)\s+(?:install|add|get)\s+([A-Za-z0-9._-]{3,})"),
    re.compile(r"\b[A-Z][A-Za-z0-9]+(?:\.[A-Za-z0-9]+)+\b"),
    re.compile(r"(?i)\b(?:role|permission|scope|cmdlet|module)\b.*?([A-Za-z][A-Za-z0-9._-]{3,})"),
]

DEPARTMENT_KEYWORDS = {
    "engineering": ["code", "debug", "test", "production", "deploy"],
    "security": ["security", "rbac", "mailbox", "postfach"],
    "finance": ["budget", "forecast", "invoice", "payment", "finance"],
    "hr": ["employee", "onboarding", "cv", "bewerbung", "hr"],
    "legal": ["contract", "vertrag", "legal"],
    "sales": ["sales", "angebot", "lead"],
    "support": ["support", "ticket"],
    "marketing": ["marketing", "copy", "content"],
    "product": ["roadmap", "product"],
    "data": ["kpi", "report", "analysis"],
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


def _infer_department(text: str, fallback: str | None = None) -> str | None:
    haystack = text.lower()
    for department, keywords in DEPARTMENT_KEYWORDS.items():
        if any(keyword in haystack for keyword in keywords):
            return department
    return fallback


def _snippet(text: str, start: int, end: int, padding: int = 60) -> str:
    left = max(0, start - padding)
    right = min(len(text), end + padding)
    return text[left:right].strip()


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
            raw = json.load(handle)

        # Normalize: list-format files (e.g. wildchat) contain multiple conversations
        payloads: list[dict] = []
        if isinstance(raw, list):
            for entry in raw:
                if isinstance(entry, dict) and "conversation" in entry:
                    # wildchat format: {conversation_hash, model, conversation: [{content, role}]}
                    payloads.append({
                        "title": entry.get("conversation_hash", path.stem),
                        "author": entry.get("model", path.stem.split("_")[0]),
                        "date": entry.get("timestamp"),
                        "messages": [
                            {"id": f"{entry.get('conversation_hash', '')}-{i}",
                             "author": msg.get("role", "unknown"),
                             "content": msg.get("content", "")}
                            for i, msg in enumerate(entry["conversation"])
                            if isinstance(msg, dict)
                        ],
                    })
        elif isinstance(raw, dict):
            payloads.append(raw)

        for payload in payloads:
            messages: list[ConversationMessage] = []
            for message in payload.get("messages", []):
                if not isinstance(message, dict):
                    continue
                content = _normalize_text(message.get("content"))
                if not content:
                    continue
                messages.append(
                    ConversationMessage(
                        id=str(message.get("id") or _hash_id(path.stem, content[:32])),
                        author=str(message.get("author") or "unknown"),
                        content=content,
                    )
                )

            records.append(
                ConversationRecord(
                    conversation_id=str(payload.get("url") or payload.get("title") or path.stem),
                    provider=_normalize_family(str(payload.get("author") or path.stem.split("_")[0])),
                    title=str(payload.get("title") or path.stem),
                    exported_at=_parse_timestamp(payload.get("date")),
                    messages=tuple(messages),
                )
            )

    return tuple(records)


@lru_cache(maxsize=1)
def _load_findings(root: str) -> tuple[FindingRecord, ...]:
    findings: list[FindingRecord] = []
    for conversation in _load_conversations(root):
        department = _infer_department(conversation.title or conversation.conversation_id)
        for message in conversation.messages:
            text = message.content
            role = "assistant" if message.author.lower() in {"assistant", "ai", "model", "bot"} else "user"

            for category, (pattern, severity) in SECRET_PATTERNS.items():
                for match in pattern.finditer(text):
                    match_value = match.group(1) if match.groups() else match.group(0)
                    findings.append(
                        FindingRecord(
                            id=_hash_id(conversation.conversation_id, message.id, "secret", category, match_value),
                            type="secret",
                            severity=severity,
                            category=category,
                            model=conversation.provider,
                            provider=conversation.provider,
                            conversation_id=conversation.conversation_id,
                            message_id=message.id,
                            role=role,
                            timestamp=conversation.exported_at or datetime.now(timezone.utc),
                            match_value=match_value,
                            match_context=_snippet(text, match.start(), match.end()),
                            source_field="content",
                            confidence=0.96 if severity == "critical" else 0.9,
                            department=department,
                        )
                    )

            for category, (pattern, severity) in PII_PATTERNS.items():
                for match in pattern.finditer(text):
                    match_value = match.group(0)
                    findings.append(
                        FindingRecord(
                            id=_hash_id(conversation.conversation_id, message.id, "pii", category, match_value),
                            type="pii",
                            severity=severity,
                            category=category,
                            model=conversation.provider,
                            provider=conversation.provider,
                            conversation_id=conversation.conversation_id,
                            message_id=message.id,
                            role=role,
                            timestamp=conversation.exported_at or datetime.now(timezone.utc),
                            match_value=match_value,
                            match_context=_snippet(text, match.start(), match.end()),
                            source_field="content",
                            confidence=0.88,
                            department=department,
                        )
                    )

            if role == "assistant":
                for pattern in SLOPSQUAT_PATTERNS:
                    for match in pattern.finditer(text):
                        match_value = match.group(1) if match.groups() else match.group(0)
                        severity = "critical" if any(token in match_value.lower() for token in ["role", "endpoint", "password"]) else "high"
                        findings.append(
                            FindingRecord(
                                id=_hash_id(conversation.conversation_id, message.id, "slopsquat", match_value),
                                type="slopsquat",
                                severity=severity,
                                category="hallucinated_package",
                                model=conversation.provider,
                                provider=conversation.provider,
                                conversation_id=conversation.conversation_id,
                                message_id=message.id,
                                role=role,
                                timestamp=conversation.exported_at or datetime.now(timezone.utc),
                                match_value=match_value,
                                match_context=_snippet(text, match.start(), match.end()),
                                source_field="content",
                                confidence=0.8,
                                department=department,
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
        findings = [replace(finding) for finding in _load_findings(str(self._root))]
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
