from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CompanyReferenceRule:
    id: str
    source_table: str
    source_record_id: str
    source_field: str
    label: str
    category: str
    severity: str
    pattern: str
    value: str


@dataclass(frozen=True)
class ChatMessageRecord:
    source_file: str
    conversation_key: str
    conversation_title: str | None
    provider: str
    model_name: str | None
    message_id: str
    message_timestamp: datetime | None
    author: str
    role: str
    source_text: str


@dataclass(frozen=True)
class DeterministicMatchRecord:
    id: str
    analysis_run_id: str
    department: str | None
    source_file: str
    conversation_key: str
    conversation_title: str | None
    provider: str
    model_name: str | None
    message_id: str
    message_timestamp: datetime | None
    author: str
    role: str
    source_field: str
    company_rule_id: str
    company_label: str
    company_category: str
    company_source_table: str
    company_source_field: str
    matched_text: str
    match_context: str
    severity: str
    confidence: float


@dataclass(frozen=True)
class ConversationSummaryRecord:
    analysis_run_id: str
    conversation_key: str
    department: str | None
    provider: str
    model_name: str | None
    match_count: int
    secret_count: int
    pii_count: int
    financial_count: int
    labels_json: str
    highest_severity: str

@dataclass(frozen=True)
class ConversationInsightRecord:
    id: str
    chat_id: int
    run_id: str
    risk_score: int
    risk_factors: list[str]
    summary: str
    created_at: datetime | None

@dataclass(frozen=True)
class RecommendationRecord:
    id: str
    category: str
    title: str
    description: str
    impact_score: int
    target_audience: str
    status: str
    created_at: datetime | None

