from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class DashboardFilters:
    time_range: str = "month"
    dimension: str = "department"
    metric: str = "avgWordCountPerSession"
    start_date: datetime | None = None
    end_date: datetime | None = None
    department: str | None = None
    model: str | None = None
    provider: str | None = None
    category: str | None = None
    severity: str | None = None
    status: str | None = None
    limit: int = 50
    offset: int = 0
    sort_by: str = "timestamp"


@dataclass(frozen=True)
class UsageRecord:
    id: str
    user_id_hash: str
    department_id: str
    tool_name: str
    model_name: str
    usage_start: datetime
    usage_end: datetime
    token_count: int
    cost: float
    purpose: str = ""
    region: str | None = None
    word_count: int = 0


@dataclass(frozen=True)
class ConversationMessage:
    id: str
    author: str
    content: str


@dataclass(frozen=True)
class ConversationRecord:
    conversation_id: str
    provider: str
    title: str
    exported_at: datetime | None
    messages: tuple[ConversationMessage, ...]


@dataclass
class FindingRecord:
    id: str
    type: str
    severity: str
    category: str
    model: str
    provider: str
    conversation_id: str
    message_id: str
    role: str
    timestamp: datetime
    match_value: str
    match_context: str
    source_field: str
    confidence: float
    department: str | None = None
    status: str = "open"
    notes: str | None = None
    extra: dict[str, str] = field(default_factory=dict)
