# Analysis Pipeline — Data Model & Architecture

## Overview

```
Chat exports (JSON/JSONL/MD)
        ↓  chat_import.py
   chats table  ←──────────────────── source of truth
        ↓  run_analysis_worker.py (polls every 15s)
        ├── Anna: secrets + PII (deterministic, regex)
        ├── Finn: slopsquatting / malicious libraries (registry lookup)
        └── Lars: trivial / sensitivity / complexity (Gemini Flash → local LLM in prod)
        ↓  all write to
  findings table  ←─────────────────── per-message findings
        ↓  refresh_dashboard_views()
  materialized views  ←────────────── pre-computed, frontend-facing
        ↓
   API endpoints
        ↓
   Frontend dashboard
```

---

## Database Schema

### `chats` — ingested messages

Populated by `chat_import.py`. One row per message per conversation.

| Column | Type | Notes |
|---|---|---|
| `id` | BIGSERIAL PK | |
| `source_file` | TEXT | Absolute path of source file |
| `source_format` | VARCHAR(20) | `json`, `jsonl`, `markdown` |
| `provider` | VARCHAR(50) | `chatgpt`, `gemini`, `claude_code`, `pi_agent`, `antigravity` |
| `conversation_key` | TEXT | Groups messages into conversations |
| `conversation_title` | TEXT | Human-readable title if available |
| `conversation_slug` | TEXT | Machine-readable slug (Claude Code) |
| `export_author` | VARCHAR(50) | Exporter identity |
| `model_name` | VARCHAR(100) | e.g. `gpt-4o`, `claude-opus-4-6` |
| `conversation_timestamp` | TIMESTAMPTZ | When the conversation started |
| `message_id` | TEXT | Provider-specific message ID |
| `parent_message_id` | TEXT | For conversation tree linking |
| `message_index` | INTEGER | Position in conversation |
| `message_timestamp` | TIMESTAMPTZ | When this message was sent |
| `author` | VARCHAR(20) | `user` or `model` |
| `role` | VARCHAR(20) | Raw role string from provider |
| `language` | VARCHAR(50) | Detected language |
| `user_text` | TEXT | Raw message content |
| `user_text_clean` | TEXT | Cleaned: URLs, emails, obvious secrets redacted |
| `user_text_hash` | CHAR(64) | SHA-256 of cleaned text (deduplication) |
| `metadata` | JSONB | Provider-specific extra fields |

**Unique constraint:** `(source_file, conversation_key, message_id)` — idempotent ingestion.

**Indexes:** `provider`, `conversation_timestamp`, `user_text_hash`

---

### `findings` — analysis results

Populated by all analyzers. One row per finding per message.

| Column | Type | Notes |
|---|---|---|
| `id` | BIGSERIAL PK | |
| `chat_id` | BIGINT FK → chats.id | |
| `analyzer` | VARCHAR(50) | See analyzer registry below |
| `category` | VARCHAR(50) | See categories below |
| `severity` | VARCHAR(20) | `critical`, `high`, `medium`, `low`, `info` |
| `title` | VARCHAR(500) | Human-readable finding |
| `detail` | TEXT | Explanation / context |
| `snippet` | TEXT | Matched text or relevant excerpt |
| `confidence` | REAL | 1.0 for deterministic, 0.0–1.0 for LLM |
| `meta` | JSONB | Analyzer-specific structured data |
| `created_at` | TIMESTAMPTZ | |

**Indexes:** `chat_id`, `analyzer`, `category`, `severity`

#### Analyzer registry

| `analyzer` | Owner | Type | Description |
|---|---|---|---|
| `secrets` | Anna | Deterministic | API keys, tokens, DB credentials (regex) |
| `pii` | Anna | Deterministic | Emails, names, IPs, IBANs (regex) |
| `slopsquatting` | Finn | Deterministic | Hallucinated/malicious packages (registry lookup) |
| `llm_trivial` | Lars | LLM | Productive vs wasteful usage classification |
| `llm_sensitivity` | Lars | LLM | Business-sensitive content beyond regex |
| `llm_complexity` | Lars | LLM | Conversation complexity score 1–10 |

#### Categories

| `category` | Displayed as |
|---|---|
| `security_leak` | Security Leaks |
| `content_leak` | Content / Data Leaks |
| `supply_chain` | Malicious Libraries |
| `usage_quality` | Trivial Usage |
| `complexity` | Complexity Score (scatter plot) |

---

## Materialized Views — Frontend Read Layer

**Why views, not separate tables?** Materialized views are *defined* by their source query — correctness is guaranteed by construction. A separate summary table would require manual `TRUNCATE + INSERT` logic that duplicates the query and introduces sync bugs. Since the dashboard is batch-refreshed (not real-time), `REFRESH MATERIALIZED VIEW CONCURRENTLY` gives us atomic, zero-downtime updates with no extra application code. Performance after refresh is identical — both are just stored rows on disk.

Refreshed via `SELECT refresh_dashboard_views()` after each worker run. Read-only from the frontend. Instant queries — no joins at request time.

| View | API endpoint | Purpose |
|---|---|---|
| `mv_dashboard_overview` | `GET /api/overview` | Single-row totals: messages, conversations, findings by severity |
| `mv_findings_by_category` | `GET /api/findings` | Finding counts by category + severity + provider + model |
| `mv_provider_stats` | `GET /api/providers` | Per-provider message count, leak counts, avg complexity |
| `mv_findings_timeline` | `GET /api/trends` | Findings per day per category (sparklines) |
| `mv_top_findings` | `GET /api/alerts` | 100 most recent critical/high findings (alert feed) |
| `mv_scatter_complexity_leaks` | `GET /api/scatter` | Per-conversation complexity vs leak count (scatter plot) |

---

## Analyzer Contract

All analyzers follow the same interface so the worker can call them uniformly:

```python
from app.application.services.llm_extraction import Finding

async def analyze_X(chat_ids: list[int], messages: list[str]) -> list[Finding]:
    findings = []
    for i, (chat_id, message) in enumerate(zip(chat_ids, messages)):
        # ... analysis logic ...
        if finding_detected:
            findings.append(Finding(
                chat_id=chat_id,
                analyzer="your_analyzer_name",  # must match registry above
                category="security_leak",        # must match categories above
                severity="high",                 # critical | high | medium | low | info
                title="Short human-readable title",
                detail="Explanation of what was found",
                snippet=message[:300],
                confidence=1.0,                  # 1.0 for deterministic
                meta={},                         # any structured data
            ))
    return findings
```

Plug into `run_analysis_worker.py` → `run_deterministic()`.

---

## LLM Strategy

| Environment | Model | Rationale |
|---|---|---|
| Hackathon demo | `gemini-2.0-flash` | Already integrated, fast, cheap |
| Production (EU) | Mistral via La Plateforme | EU-domiciled, GDPR-native, low cost |
| Production (sovereign) | Ollama + Mistral/LLaMA local | Zero data egress, on-prem |

The LLM client is configured via `GEMINI_MODEL` env var. Swapping providers = change config, not code.

---

## Operations

```bash
# Initial setup
psql -U postgres -d hackathon -f src/backend/scripts/postgres/002_chats_schema.sql
psql -U postgres -d hackathon -f src/backend/scripts/postgres/003_findings_schema.sql
psql -U postgres -d hackathon -f src/backend/scripts/postgres/004_dashboard_views.sql

# Ingest chat exports
python src/backend/scripts/run_chat_import.py --dir chat-exports/

# Run analysis (single pass)
python src/backend/scripts/run_analysis_worker.py

# Run analysis (continuous)
python src/backend/scripts/run_analysis_worker.py --loop --interval 15

# Wipe findings only (re-run analysis with new prompts)
python src/backend/scripts/wipe_database.py --only findings --confirm

# Full wipe (demo reset)
python src/backend/scripts/wipe_database.py --confirm
```
