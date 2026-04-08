"""Deterministic extraction — regex-based secret, PII, and slopsquatting detection.

Reads messages from the `chats` table, runs pattern matching, and writes
findings to the `findings` table (same contract as llm_extraction.py).

Analyzers:
  1. secrets — API keys, tokens, passwords, connection strings, private keys
  2. pii — emails, internal IPs, phone numbers, internal paths/URLs
  3. slopsquatting — hallucinated package names in install commands

Usage:
    from app.application.services.deterministic_extraction import run_deterministic_extraction
    await run_deterministic_extraction(batch_size=50)
"""

from __future__ import annotations

import json
import logging
import re

from sqlalchemy import text

from app.application.services.llm_extraction import Finding, _save_findings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pattern definitions
# ---------------------------------------------------------------------------

SECRET_PATTERNS: dict[str, tuple[re.Pattern[str], str, str]] = {
    # name -> (pattern, severity, human title)
    "api_key": (
        re.compile(r"\b(?:sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{20,})\b"),
        "high",
        "API key detected",
    ),
    "access_token": (
        re.compile(r"\b(?:eyJ[a-zA-Z0-9_-]{20,}|xox[baprs]-[A-Za-z0-9-]{10,})\b"),
        "high",
        "Access token detected",
    ),
    "password": (
        re.compile(r"(?i)\bpassword\b\s*[:=]\s*['\"]?([^\s'\"]{6,})"),
        "high",
        "Password in plaintext",
    ),
    "private_key": (
        re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----"),
        "critical",
        "Private key detected",
    ),
    "connection_string": (
        re.compile(r"\b(?:postgres|mysql|mssql|mongodb)://\S+", re.IGNORECASE),
        "critical",
        "Database connection string",
    ),
    "webhook_url": (
        re.compile(r"https?://hooks\.[^\s]+", re.IGNORECASE),
        "medium",
        "Webhook URL detected",
    ),
    "client_secret": (
        re.compile(r"(?i)\bclient[_-]?secret\b\s*[:=]\s*['\"]?([^\s'\"]{6,})"),
        "critical",
        "Client secret detected",
    ),
    "azure_tenant": (
        re.compile(r"(?i)\btenant[_-]?id\b\s*[:=]\s*['\"]?([0-9a-f-]{16,})"),
        "medium",
        "Azure tenant ID detected",
    ),
}

PII_PATTERNS: dict[str, tuple[re.Pattern[str], str, str]] = {
    "email": (
        re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
        "high",
        "Email address detected",
    ),
    "ip_address": (
        re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
        "high",
        "IP address detected",
    ),
    "phone_number": (
        re.compile(r"\b(?:\+?\d{1,3}[\s-]?)?(?:\d[\s-]?){7,14}\b"),
        "medium",
        "Phone number detected",
    ),
    "internal_path": (
        re.compile(r"(?:[A-Za-z]:\\|/)(?:[\w.-]+[/\\]){2,}[\w.-]+"),
        "medium",
        "Internal file path detected",
    ),
}

SLOPSQUAT_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"(?i)\b(?:pip|npm|yarn|pnpm|cargo|go get|dotnet add)\s+(?:install|add|get)\s+([A-Za-z0-9._-]{3,})"), "Package install command"),
    (re.compile(r"(?i)(?:import|from|require)\s*\(?\s*['\"]([A-Za-z][A-Za-z0-9._-]{2,})['\"]"), "Import statement"),
]


# ---------------------------------------------------------------------------
# Snippet helper
# ---------------------------------------------------------------------------

def _snippet(text: str, start: int, end: int, padding: int = 80) -> str:
    left = max(0, start - padding)
    right = min(len(text), end + padding)
    return text[left:right].strip()


# ---------------------------------------------------------------------------
# Analyzer functions — same signature as llm_extraction analyzers
# ---------------------------------------------------------------------------

async def analyze_secrets(chat_ids: list[int], messages: list[str]) -> list[Finding]:
    """Detect API keys, tokens, passwords, connection strings via regex."""
    findings = []
    for i, (chat_id, msg) in enumerate(zip(chat_ids, messages)):
        if not msg:
            continue
        for name, (pattern, severity, title) in SECRET_PATTERNS.items():
            for match in pattern.finditer(msg):
                matched_text = match.group(1) if match.groups() else match.group(0)
                findings.append(Finding(
                    chat_id=chat_id,
                    analyzer="secrets",
                    category="security_leak",
                    severity=severity,
                    title=title,
                    detail=f"Pattern: {name}",
                    snippet=_snippet(msg, match.start(), match.end()),
                    confidence=1.0,
                    meta={"pattern": name, "matched_text": matched_text[:50]},
                ))
    return findings


async def analyze_pii(chat_ids: list[int], messages: list[str]) -> list[Finding]:
    """Detect emails, IPs, phone numbers, internal paths via regex."""
    findings = []
    for i, (chat_id, msg) in enumerate(zip(chat_ids, messages)):
        if not msg:
            continue
        for name, (pattern, severity, title) in PII_PATTERNS.items():
            for match in pattern.finditer(msg):
                matched_text = match.group(0)
                findings.append(Finding(
                    chat_id=chat_id,
                    analyzer="pii",
                    category="content_leak",
                    severity=severity,
                    title=title,
                    detail=f"Pattern: {name}",
                    snippet=_snippet(msg, match.start(), match.end()),
                    confidence=1.0,
                    meta={"pattern": name, "matched_text": matched_text[:50]},
                ))
    return findings


async def analyze_slopsquatting(chat_ids: list[int], messages: list[str]) -> list[Finding]:
    """Detect potentially hallucinated package names in install/import statements."""
    findings = []
    for i, (chat_id, msg) in enumerate(zip(chat_ids, messages)):
        if not msg:
            continue
        for pattern, description in SLOPSQUAT_PATTERNS:
            for match in pattern.finditer(msg):
                package_name = match.group(1) if match.groups() else match.group(0)
                findings.append(Finding(
                    chat_id=chat_id,
                    analyzer="slopsquatting",
                    category="supply_chain",
                    severity="medium",
                    title=f"Potential slopsquatting: {package_name}",
                    detail=description,
                    snippet=_snippet(msg, match.start(), match.end()),
                    confidence=0.8,
                    meta={"package": package_name, "source": description},
                ))
    return findings


# ---------------------------------------------------------------------------
# Main entry point — same contract as run_llm_extraction
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


async def run_deterministic_extraction(
    batch_size: int = 50,
    analyzers: list[str] | None = None,
) -> dict[str, int]:
    """Run deterministic extraction on unanalyzed chat messages.

    Args:
        batch_size: Number of messages to process per analyzer per run.
        analyzers: Which analyzers to run. Default: all three.

    Returns:
        Dict of analyzer name -> number of findings produced.
    """
    if analyzers is None:
        analyzers = ["secrets", "pii", "slopsquatting"]

    analyzer_fns = {
        "secrets": analyze_secrets,
        "pii": analyze_pii,
        "slopsquatting": analyze_slopsquatting,
    }

    from app.infrastructure.database import async_session_factory

    stats: dict[str, int] = {}

    for analyzer_name in analyzers:
        fn = analyzer_fns.get(analyzer_name)
        if not fn:
            continue

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
