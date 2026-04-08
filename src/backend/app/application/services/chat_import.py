"""Chat export import service.

This module contains business logic for parsing and preprocessing chat history
from multiple providers into normalized rows for the `chats` table.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import text

URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
SECRET_RE = re.compile(r"\b(sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{20,})\b")
WHITESPACE_RE = re.compile(r"\s+")
SECTION_RE = re.compile(r"^###\s+(?P<header>.+?)\s*$", re.MULTILINE)


@dataclass
class ChatRow:
    source_file: str
    source_format: str
    provider: str
    conversation_key: str
    conversation_title: str | None
    conversation_slug: str | None
    export_author: str | None
    model_name: str | None
    conversation_timestamp: datetime | None
    message_id: str
    parent_message_id: str | None
    message_index: int
    message_timestamp: datetime | None
    author: str
    role: str
    language: str | None
    user_text: str
    user_text_clean: str
    user_text_hash: str
    metadata_json: str


@dataclass
class ImportStats:
    processed_local_files: int
    extracted_messages: int
    providers: dict[str, int]
    top_files: list[tuple[str, int]]
    inserted_or_updated: int = 0


def parse_timestamp(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value) / 1000.0, tz=timezone.utc)
    if isinstance(value, str):
        try:
            normalized = value.replace("Z", "+00:00")
            dt = datetime.fromisoformat(normalized)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            return None
    return None


def clean_user_text(raw: str) -> str:
    if not isinstance(raw, str):
        raw = str(raw)
    # Remove null bytes which cause UTF-8 encoding issues - do this first
    cleaned = raw.replace("\x00", "")
    cleaned = cleaned.strip()
    cleaned = URL_RE.sub("[REDACTED_URL]", cleaned)
    cleaned = EMAIL_RE.sub("[REDACTED_EMAIL]", cleaned)
    cleaned = SECRET_RE.sub("[REDACTED_SECRET]", cleaned)
    cleaned = WHITESPACE_RE.sub(" ", cleaned)
    # Final pass to remove any remaining null bytes
    cleaned = cleaned.replace("\x00", "")
    return cleaned


def detect_provider(file_name: str, fallback: str | None = None) -> str:
    lower = file_name.lower()
    if lower.startswith("chatgpt_"):
        return "chatgpt"
    if lower.startswith("gemini_"):
        return "gemini"
    if lower.startswith("antigravity"):
        return "antigravity"
    return (fallback or "unknown").lower()


def normalize_author(role_value: Any) -> str | None:
    if role_value is None:
        return None
    normalized = str(role_value).strip().lower()
    if normalized in {"user", "human"}:
        return "user"
    if normalized in {"assistant", "model", "ai", "bot"}:
        return "model"
    return None


def extract_text_from_content(content: Any) -> str:
    if isinstance(content, str):
        return content.replace("\x00", "")
    if isinstance(content, dict):
        for key in ("text", "content", "prompt", "message"):
            value = content.get(key)
            if isinstance(value, str):
                return value.replace("\x00", "")
        return ""
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block.replace("\x00", ""))
                continue
            if not isinstance(block, dict):
                continue
            block_type = str(block.get("type", "")).lower()
            if block_type in {"text", "input_text", "user_text"} and isinstance(block.get("text"), str):
                parts.append(block["text"].replace("\x00", ""))
            elif isinstance(block.get("content"), str):
                parts.append(block["content"].replace("\x00", ""))
        return "\n".join(p for p in parts if p.strip())
    return ""


def build_row(
    source_file: str,
    source_format: str,
    provider: str,
    conversation_key: str,
    conversation_title: str | None,
    conversation_slug: str | None,
    export_author: str | None,
    model_name: str | None,
    conversation_timestamp: datetime | None,
    message_id: str,
    parent_message_id: str | None,
    message_index: int,
    message_timestamp: datetime | None,
    author: str,
    role: str,
    language: str | None,
    user_text: str,
    metadata: dict[str, Any],
) -> ChatRow:
    # Clean null bytes from raw user_text first
    user_text = user_text.replace("\x00", "")
    user_text_clean = clean_user_text(user_text)
    user_text_hash = hashlib.sha256(user_text_clean.encode("utf-8")).hexdigest()
    
    # Clean metadata values to remove null bytes before JSON serialization
    cleaned_metadata = {}
    for k, v in metadata.items():
        if isinstance(v, str):
            cleaned_metadata[k] = v.replace("\x00", "")
        else:
            cleaned_metadata[k] = v
    
    metadata_json = json.dumps(cleaned_metadata, ensure_ascii=True)

    return ChatRow(
        source_file=source_file,
        source_format=source_format,
        provider=provider,
        conversation_key=conversation_key,
        conversation_title=conversation_title,
        conversation_slug=conversation_slug,
        export_author=export_author,
        model_name=model_name,
        conversation_timestamp=conversation_timestamp,
        message_id=message_id,
        parent_message_id=parent_message_id,
        message_index=message_index,
        message_timestamp=message_timestamp,
        author=author,
        role=role,
        language=language,
        user_text=user_text,
        user_text_clean=user_text_clean,
        user_text_hash=user_text_hash,
        metadata_json=metadata_json,
    )


def extract_standard_export_rows(path: Path, payload: dict[str, Any]) -> list[ChatRow]:
    rows: list[ChatRow] = []
    messages = payload.get("messages", [])

    provider = detect_provider(path.name, payload.get("author"))
    conversation_key = payload.get("url") or f"{path.stem}"
    conversation_title = payload.get("title")
    export_author = payload.get("author")
    conversation_ts = parse_timestamp(payload.get("date"))

    for idx, message in enumerate(messages):
        role_value = message.get("author")
        author = normalize_author(role_value)
        if author is None:
            continue

        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            continue

        msg_id = str(message.get("id") or f"{author}-{idx}")
        metadata = {
            "source": "standard-export",
            "url": payload.get("url"),
            "tag_count": len(payload.get("tags", [])) if isinstance(payload.get("tags"), list) else 0,
            "message_total": payload.get("count"),
            "exporter": payload.get("exporter"),
        }

        rows.append(
            build_row(
                source_file=path.as_posix(),
                source_format="json",
                provider=provider,
                conversation_key=conversation_key,
                conversation_title=conversation_title,
                conversation_slug=None,
                export_author=export_author,
                model_name=None,
                conversation_timestamp=conversation_ts,
                message_id=msg_id,
                parent_message_id=None,
                message_index=idx,
                message_timestamp=None,
                author=author,
                role=str(role_value or author).lower(),
                language=None,
                user_text=content,
                metadata=metadata,
            )
        )

    return rows


def extract_wildchat_rows(path: Path, payload: list[dict[str, Any]]) -> list[ChatRow]:
    rows: list[ChatRow] = []

    for conv_idx, conversation in enumerate(payload):
        model_name = conversation.get("model")
        language = conversation.get("language")
        conversation_key = str(conversation.get("conversation_hash") or f"{path.stem}-{conv_idx}")
        conversation_title = f"wildchat-{conversation_key[:12]}"
        conversation_ts = parse_timestamp(conversation.get("timestamp"))

        turns = conversation.get("conversation", [])
        for msg_idx, message in enumerate(turns):
            role_value = message.get("role")
            author = normalize_author(role_value)
            if author is None:
                continue

            content = message.get("content")
            if not isinstance(content, str) or not content.strip():
                continue

            msg_id = str(message.get("turn_identifier") or f"{author}-{msg_idx}")
            metadata = {
                "source": "wildchat",
                "turn": conversation.get("turn"),
                "conversation_hash": conversation.get("conversation_hash"),
                "redacted": conversation.get("redacted"),
                "toxic": conversation.get("toxic"),
            }

            rows.append(
                build_row(
                    source_file=path.as_posix(),
                    source_format="json",
                    provider="chatgpt",
                    conversation_key=conversation_key,
                    conversation_title=conversation_title,
                    conversation_slug=None,
                    export_author=None,
                    model_name=model_name,
                    conversation_timestamp=conversation_ts,
                    message_id=msg_id,
                    parent_message_id=None,
                    message_index=msg_idx,
                    message_timestamp=parse_timestamp(message.get("timestamp")),
                    author=author,
                    role=str(role_value or author).lower(),
                    language=language,
                    user_text=content,
                    metadata=metadata,
                )
            )

    return rows


def extract_antigravity_markdown_rows(path: Path) -> list[ChatRow]:
    text_content = path.read_text(encoding="utf-8")
    matches = list(SECTION_RE.finditer(text_content))
    if not matches:
        return []

    rows: list[ChatRow] = []
    conversation_key = path.stem

    message_idx = 0
    for idx, match in enumerate(matches):
        header = match.group("header").strip().lower()
        if header in {"user input", "user prompt", "prompt"}:
            author = "user"
        elif header in {"assistant response", "model output", "assistant output", "response"}:
            author = "model"
        else:
            continue

        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text_content)
        block = text_content[start:end].strip()
        if not block:
            continue

        rows.append(
            build_row(
                source_file=path.as_posix(),
                source_format="markdown",
                provider="antigravity",
                conversation_key=conversation_key,
                conversation_title=path.stem,
                conversation_slug=None,
                export_author="antigravity",
                model_name=None,
                conversation_timestamp=None,
                message_id=f"user-md-{message_idx}",
                parent_message_id=None,
                message_index=message_idx,
                message_timestamp=None,
                author=author,
                role=author,
                language=None,
                user_text=block,
                metadata={"source": "antigravity-markdown"},
            )
        )
        message_idx += 1

    return rows


def extract_claude_history_rows(path: Path) -> list[ChatRow]:
    rows: list[ChatRow] = []
    if not path.exists():
        return rows

    with path.open("r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            role_value = event.get("role") or event.get("author") or event.get("type")
            author = normalize_author(role_value)
            if author is None:
                author = "user"

            text_value = extract_text_from_content(event.get("prompt") or event.get("content") or event.get("text"))
            if not text_value.strip():
                continue

            conv_key = str(event.get("sessionId") or event.get("conversationId") or path.stem)
            rows.append(
                build_row(
                    source_file=path.as_posix(),
                    source_format="jsonl",
                    provider="claude_code",
                    conversation_key=conv_key,
                    conversation_title="claude-history",
                    conversation_slug=None,
                    export_author=None,
                    model_name=event.get("model"),
                    conversation_timestamp=parse_timestamp(event.get("timestamp") or event.get("createdAt")),
                    message_id=str(event.get("id") or event.get("uuid") or f"claude-history-{idx}"),
                    parent_message_id=None,
                    message_index=idx,
                    message_timestamp=parse_timestamp(event.get("timestamp") or event.get("createdAt")),
                    author=author,
                    role=str(role_value or author).lower(),
                    language=event.get("language"),
                    user_text=text_value,
                    metadata={"source": "claude-history-jsonl"},
                )
            )

    return rows


def extract_claude_projects_rows(root_dir: Path) -> list[ChatRow]:
    rows: list[ChatRow] = []
    if not root_dir.exists() or not root_dir.is_dir():
        return rows

    for file_path in root_dir.rglob("*.jsonl"):
        message_index = 0
        with file_path.open("r", encoding="utf-8") as f:
            for line_idx, line in enumerate(f):
                if not line.strip():
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue

                role_value = event.get("type") or event.get("role")
                author = normalize_author(role_value)
                if author is None:
                    continue

                text_value = extract_text_from_content(event.get("message") or event.get("content"))
                if not text_value.strip():
                    continue

                conv_key = str(event.get("sessionId") or event.get("conversationId") or file_path.stem)
                rows.append(
                    build_row(
                        source_file=file_path.as_posix(),
                        source_format="jsonl",
                        provider="claude_code",
                        conversation_key=conv_key,
                        conversation_title=None,
                        conversation_slug=file_path.parent.name,
                        export_author=None,
                        model_name=event.get("model"),
                        conversation_timestamp=parse_timestamp(event.get("timestamp")),
                        message_id=str(event.get("uuid") or event.get("id") or f"claude-{author}-{line_idx}"),
                        parent_message_id=event.get("parentUuid") or event.get("parentId"),
                        message_index=message_index,
                        message_timestamp=parse_timestamp(event.get("timestamp")),
                        author=author,
                        role=str(role_value or author).lower(),
                        language=None,
                        user_text=text_value,
                        metadata={
                            "source": "claude-project-jsonl",
                            "cwd": event.get("cwd"),
                            "git_branch": event.get("gitBranch"),
                            "permission_mode": event.get("permissionMode"),
                        },
                    )
                )
                message_index += 1

    return rows


def extract_pi_agent_rows(root_dir: Path) -> list[ChatRow]:
    rows: list[ChatRow] = []
    if not root_dir.exists() or not root_dir.is_dir():
        return rows

    for file_path in root_dir.rglob("*.jsonl"):
        current_model: str | None = None
        message_index = 0

        with file_path.open("r", encoding="utf-8") as f:
            for line_idx, line in enumerate(f):
                if not line.strip():
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue

                event_type = str(event.get("type", "")).lower()
                if event_type == "model_change":
                    current_model = event.get("model")
                    continue

                if event_type != "message":
                    continue

                role_value = event.get("role")
                author = normalize_author(role_value)
                if author is None:
                    continue

                text_value = extract_text_from_content(event.get("content") or event.get("message") or event.get("text"))
                if not text_value.strip():
                    continue

                conv_key = str(event.get("session_id") or event.get("sessionId") or file_path.stem)
                rows.append(
                    build_row(
                        source_file=file_path.as_posix(),
                        source_format="jsonl",
                        provider="pi_agent",
                        conversation_key=conv_key,
                        conversation_title=None,
                        conversation_slug=file_path.parent.name,
                        export_author=None,
                        model_name=event.get("model") or current_model,
                        conversation_timestamp=parse_timestamp(event.get("timestamp")),
                        message_id=str(event.get("id") or f"pi-{author}-{line_idx}"),
                        parent_message_id=event.get("parentId"),
                        message_index=message_index,
                        message_timestamp=parse_timestamp(event.get("timestamp")),
                        author=author,
                        role=str(role_value or author).lower(),
                        language=event.get("language"),
                        user_text=text_value,
                        metadata={"source": "pi-agent-jsonl", "cwd": event.get("cwd")},
                    )
                )
                message_index += 1

    return rows


def extract_rows_from_local_file(path: Path) -> list[ChatRow]:
    if path.suffix.lower() == ".md":
        return extract_antigravity_markdown_rows(path)

    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    if isinstance(payload, dict) and isinstance(payload.get("messages"), list):
        return extract_standard_export_rows(path, payload)

    if isinstance(payload, list) and payload and isinstance(payload[0], dict) and "conversation" in payload[0]:
        return extract_wildchat_rows(path, payload)

    return []


def get_async_session_factory():
    from app.infrastructure.database import async_session_factory

    return async_session_factory


async def ensure_chats_table() -> None:
    create_table_sql = text(
        """
        CREATE TABLE IF NOT EXISTS chats (
            id BIGSERIAL PRIMARY KEY,
            source_file TEXT NOT NULL,
            source_format VARCHAR(20) NOT NULL DEFAULT 'json',
            provider VARCHAR(50) NOT NULL,
            conversation_key TEXT NOT NULL,
            conversation_title TEXT,
            conversation_slug TEXT,
            export_author VARCHAR(50),
            model_name VARCHAR(100),
            conversation_timestamp TIMESTAMPTZ,
            message_id TEXT NOT NULL,
            parent_message_id TEXT,
            message_index INTEGER NOT NULL,
            message_timestamp TIMESTAMPTZ,
            author VARCHAR(20) NOT NULL DEFAULT 'user',
            role VARCHAR(20) NOT NULL DEFAULT 'user',
            language VARCHAR(50),
            user_text TEXT NOT NULL,
            user_text_clean TEXT NOT NULL,
            user_text_hash CHAR(64) NOT NULL,
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (source_file, conversation_key, message_id)
        )
        """
    )

    async_session_factory = get_async_session_factory()
    async with async_session_factory() as session:
        async with session.begin():
            await session.execute(create_table_sql)
            await session.execute(text("ALTER TABLE chats ADD COLUMN IF NOT EXISTS author VARCHAR(20) NOT NULL DEFAULT 'user'"))


async def upsert_rows(rows: list[ChatRow]) -> int:
    if not rows:
        return 0

    upsert_sql = text(
        """
        INSERT INTO chats (
            source_file,
            source_format,
            provider,
            conversation_key,
            conversation_title,
            conversation_slug,
            export_author,
            model_name,
            conversation_timestamp,
            message_id,
            parent_message_id,
            message_index,
            message_timestamp,
            author,
            role,
            language,
            user_text,
            user_text_clean,
            user_text_hash,
            metadata
        ) VALUES (
            :source_file,
            :source_format,
            :provider,
            :conversation_key,
            :conversation_title,
            :conversation_slug,
            :export_author,
            :model_name,
            :conversation_timestamp,
            :message_id,
            :parent_message_id,
            :message_index,
            :message_timestamp,
            :author,
            :role,
            :language,
            :user_text,
            :user_text_clean,
            :user_text_hash,
            CAST(:metadata_json AS jsonb)
        )
        ON CONFLICT (source_file, conversation_key, message_id)
        DO UPDATE SET
            provider = EXCLUDED.provider,
            source_format = EXCLUDED.source_format,
            conversation_title = EXCLUDED.conversation_title,
            conversation_slug = EXCLUDED.conversation_slug,
            export_author = EXCLUDED.export_author,
            model_name = EXCLUDED.model_name,
            conversation_timestamp = EXCLUDED.conversation_timestamp,
            parent_message_id = EXCLUDED.parent_message_id,
            message_index = EXCLUDED.message_index,
            message_timestamp = EXCLUDED.message_timestamp,
            author = EXCLUDED.author,
            role = EXCLUDED.role,
            language = EXCLUDED.language,
            user_text = EXCLUDED.user_text,
            user_text_clean = EXCLUDED.user_text_clean,
            user_text_hash = EXCLUDED.user_text_hash,
            metadata = EXCLUDED.metadata,
            updated_at = NOW()
        """
    )

    payloads = [row.__dict__ for row in rows]

    async_session_factory = get_async_session_factory()
    async with async_session_factory() as session:
        async with session.begin():
            for item in payloads:
                await session.execute(upsert_sql, item)

    return len(payloads)


def collect_rows(
    input_dir: Path,
    claude_history: Path | None = None,
    claude_projects_dir: Path | None = None,
    pi_sessions_dir: Path | None = None,
) -> tuple[list[ChatRow], int]:
    local_files = sorted(input_dir.glob("*.json")) + sorted(input_dir.glob("*.md"))
    all_rows: list[ChatRow] = []

    for path in local_files:
        try:
            rows = extract_rows_from_local_file(path)
            all_rows.extend(rows)
        except json.JSONDecodeError:
            continue

    if claude_history:
        all_rows.extend(extract_claude_history_rows(claude_history.expanduser()))
    if claude_projects_dir:
        all_rows.extend(extract_claude_projects_rows(claude_projects_dir.expanduser()))
    if pi_sessions_dir:
        all_rows.extend(extract_pi_agent_rows(pi_sessions_dir.expanduser()))

    return all_rows, len(local_files)


def summarize_rows(rows: list[ChatRow], processed_local_files: int) -> ImportStats:
    provider_counts = Counter(row.provider for row in rows)
    source_counts = Counter(row.source_file for row in rows)
    return ImportStats(
        processed_local_files=processed_local_files,
        extracted_messages=len(rows),
        providers=dict(provider_counts),
        top_files=source_counts.most_common(5),
    )


async def import_chat_exports(
    input_dir: Path,
    dry_run: bool,
    claude_history: Path | None = None,
    claude_projects_dir: Path | None = None,
    pi_sessions_dir: Path | None = None,
) -> ImportStats:
    if not input_dir.exists() or not input_dir.is_dir():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    rows, processed_local_files = collect_rows(
        input_dir=input_dir,
        claude_history=claude_history,
        claude_projects_dir=claude_projects_dir,
        pi_sessions_dir=pi_sessions_dir,
    )

    stats = summarize_rows(rows, processed_local_files)

    if dry_run:
        return stats

    await ensure_chats_table()
    stats.inserted_or_updated = await upsert_rows(rows)
    return stats
