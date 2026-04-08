"""LLM-based extraction service.

Reads messages from the `chats` table, sends batches to Gemini Flash
for classification, and writes findings to the `findings` table.

Analysis types:
  1. Trivial question detection — is this a productive or wasteful use of AI?
  2. Sensitivity classification — does this contain business-critical content?
  3. Complexity scoring — how complex is this conversation? (for scatter plot)

Usage:
    from app.application.services.llm_extraction import run_llm_extraction
    await run_llm_extraction(batch_size=50)
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from google import genai
from sqlalchemy import text

from app.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

TRIVIAL_PROMPT = """\
You are a corporate AI usage auditor. Classify each message as either
"productive" or "trivial" for a business context.

Productive: code generation, debugging, architecture, documentation, data analysis,
professional writing, technical research, business communication.

Trivial: weather, jokes, recipes, personal travel, sports scores, entertainment
recommendations, casual chitchat, homework unrelated to work.

For each message, return a JSON object:
{
  "classification": "productive" | "trivial",
  "confidence": 0.0-1.0,
  "reason": "brief explanation"
}

Respond with a JSON array — one object per message, same order as input.
No markdown, no explanation outside the JSON.

Messages:
"""

SENSITIVITY_PROMPT = """\
You are a data loss prevention analyst. For each message, check whether it
contains business-sensitive content that should NOT be sent to external AI providers.

Look for:
- Internal project names or codenames
- Customer names, account numbers, portfolio IDs
- Internal URLs, hostnames, or infrastructure details
- Competitive intelligence or strategic plans
- Financial figures, revenue, pricing
- Employee names in business context
- Proprietary algorithms or trade secrets

For each message, return a JSON object:
{
  "contains_sensitive": true | false,
  "sensitivity_level": "none" | "low" | "medium" | "high" | "critical",
  "findings": [
    {"type": "project_name" | "customer_data" | "internal_infra" | "financial" | "competitive" | "proprietary", "detail": "what was found"}
  ]
}

Respond with a JSON array — one object per message, same order as input.
No markdown, no explanation outside the JSON.

Messages:
"""

COMPLEXITY_PROMPT = """\
You are analyzing AI conversations to score their complexity on a 1-10 scale.

Consider:
- 1-3: Simple factual questions, basic lookups, short exchanges
- 4-6: Multi-step tasks, moderate code generation, document analysis
- 7-9: Complex architecture, multi-file refactoring, deep debugging, system design
- 10: Novel research, multi-domain synthesis, production-critical decisions

For each message, return a JSON object:
{
  "complexity_score": 1-10,
  "category": "lookup" | "generation" | "analysis" | "debugging" | "architecture" | "research",
  "reason": "brief explanation"
}

Respond with a JSON array — one object per message, same order as input.
No markdown, no explanation outside the JSON.

Messages:
"""


# ---------------------------------------------------------------------------
# Gemini client
# ---------------------------------------------------------------------------

def _get_client() -> genai.Client:
    return genai.Client(api_key=settings.google_api_key)


async def _call_gemini(prompt: str, messages: list[str]) -> list[dict]:
    """Send a batch of messages to Gemini and parse JSON array response."""
    client = _get_client()

    numbered = "\n".join(f"[{i+1}] {msg[:2000]}" for i, msg in enumerate(messages))
    full_prompt = prompt + numbered

    response = await client.aio.models.generate_content(
        model=settings.gemini_model,
        contents=full_prompt,
    )

    raw = response.text.strip()
    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]

    try:
        results = json.loads(raw)
        if isinstance(results, list):
            return results
        return [results]
    except json.JSONDecodeError:
        logger.warning("Failed to parse Gemini response as JSON: %s", raw[:200])
        return []


# ---------------------------------------------------------------------------
# Analysis runners
# ---------------------------------------------------------------------------

@dataclass
class Finding:
    chat_id: int
    analyzer: str
    category: str
    severity: str
    title: str
    detail: str | None
    snippet: str | None
    confidence: float
    meta: dict


async def analyze_trivial(chat_ids: list[int], messages: list[str]) -> list[Finding]:
    """Classify messages as trivial or productive."""
    results = await _call_gemini(TRIVIAL_PROMPT, messages)
    findings = []

    for i, result in enumerate(results):
        if i >= len(chat_ids):
            break
        classification = result.get("classification", "productive")
        if classification == "trivial":
            findings.append(Finding(
                chat_id=chat_ids[i],
                analyzer="llm_trivial",
                category="usage_quality",
                severity="low",
                title="Trivial AI usage detected",
                detail=result.get("reason"),
                snippet=messages[i][:300],
                confidence=float(result.get("confidence", 0.8)),
                meta=result,
            ))

    return findings


async def analyze_sensitivity(chat_ids: list[int], messages: list[str]) -> list[Finding]:
    """Detect business-sensitive content beyond regex patterns."""
    results = await _call_gemini(SENSITIVITY_PROMPT, messages)
    findings = []

    severity_map = {"critical": "critical", "high": "high", "medium": "medium", "low": "low", "none": "info"}

    for i, result in enumerate(results):
        if i >= len(chat_ids):
            break
        if not result.get("contains_sensitive"):
            continue

        level = result.get("sensitivity_level", "medium")
        sub_findings = result.get("findings", [])
        detail_parts = [f"{f['type']}: {f['detail']}" for f in sub_findings if isinstance(f, dict)]

        findings.append(Finding(
            chat_id=chat_ids[i],
            analyzer="llm_sensitivity",
            category="content_leak",
            severity=severity_map.get(level, "medium"),
            title=f"Sensitive content detected ({level})",
            detail="; ".join(detail_parts) if detail_parts else None,
            snippet=messages[i][:300],
            confidence=0.85,
            meta=result,
        ))

    return findings


async def analyze_complexity(chat_ids: list[int], messages: list[str]) -> list[Finding]:
    """Score conversation complexity for the scatter plot."""
    results = await _call_gemini(COMPLEXITY_PROMPT, messages)
    findings = []

    for i, result in enumerate(results):
        if i >= len(chat_ids):
            break
        score = result.get("complexity_score", 5)
        findings.append(Finding(
            chat_id=chat_ids[i],
            analyzer="llm_complexity",
            category="complexity",
            severity="info",
            title=f"Complexity: {score}/10 ({result.get('category', 'unknown')})",
            detail=result.get("reason"),
            snippet=None,
            confidence=0.9,
            meta=result,
        ))

    return findings


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

INSERT_FINDING = text("""
    INSERT INTO findings (chat_id, analyzer, category, severity, title, detail, snippet, confidence, meta)
    VALUES (:chat_id, :analyzer, :category, :severity, :title, :detail, :snippet, :confidence, CAST(:meta AS jsonb))
    ON CONFLICT DO NOTHING
""")


async def _save_findings(findings: list[Finding]) -> int:
    if not findings:
        return 0

    from app.infrastructure.database import async_session_factory

    async with async_session_factory() as session:
        async with session.begin():
            for f in findings:
                await session.execute(INSERT_FINDING, {
                    "chat_id": f.chat_id,
                    "analyzer": f.analyzer,
                    "category": f.category,
                    "severity": f.severity,
                    "title": f.title,
                    "detail": f.detail,
                    "snippet": f.snippet,
                    "confidence": f.confidence,
                    "meta": json.dumps(f.meta, ensure_ascii=True),
                })

    return len(findings)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

FETCH_UNANALYZED = text("""
    SELECT c.id, c.user_text_clean
    FROM chats c
    WHERE c.author = 'user'
      AND NOT EXISTS (
          SELECT 1 FROM findings f
          WHERE f.chat_id = c.id AND f.analyzer = :analyzer
      )
    ORDER BY c.id
    LIMIT :batch_size
""")


async def run_llm_extraction(
    batch_size: int = 20,
    analyzers: list[str] | None = None,
) -> dict[str, int]:
    """Run LLM extraction on unanalyzed chat messages.

    Args:
        batch_size: Number of messages to process per analyzer per run.
        analyzers: Which analyzers to run. Default: all three.

    Returns:
        Dict of analyzer name -> number of findings produced.
    """
    if analyzers is None:
        analyzers = ["llm_trivial", "llm_sensitivity", "llm_complexity"]

    analyzer_fns = {
        "llm_trivial": analyze_trivial,
        "llm_sensitivity": analyze_sensitivity,
        "llm_complexity": analyze_complexity,
    }

    from app.infrastructure.database import async_session_factory

    stats: dict[str, int] = {}

    for analyzer_name in analyzers:
        fn = analyzer_fns.get(analyzer_name)
        if not fn:
            continue

        # Fetch unanalyzed messages
        async with async_session_factory() as session:
            result = await session.execute(FETCH_UNANALYZED, {
                "analyzer": analyzer_name,
                "batch_size": batch_size,
            })
            rows = result.fetchall()

        if not rows:
            stats[analyzer_name] = 0
            continue

        chat_ids = [row[0] for row in rows]
        messages = [row[1] for row in rows]

        logger.info("Running %s on %d messages", analyzer_name, len(messages))

        findings = await fn(chat_ids, messages)
        saved = await _save_findings(findings)
        stats[analyzer_name] = saved

        logger.info("%s: %d findings saved", analyzer_name, saved)

    return stats
