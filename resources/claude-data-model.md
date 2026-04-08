# Claude Code & Pi Agent Data Model Reference

> **Purpose:** Complete reference for where conversational AI data is stored locally, what schemas are used, and how to query it for dashboard/monitoring applications.

---

## Storage Locations Overview

```
~/.claude/
├── history.jsonl              # Raw prompt history (no metadata)
├── projects/                  # Per-project conversation sessions
│   └── -home-<user>-.../
│       └── <session-id>.jsonl # Full conversation with usage data
├── sessions/                  # Session registry (metadata only)
│   └── <pid>.json             # PID → sessionId mapping
│
~/.pi/
├── agent/
│   ├── sessions/              # Pi agent conversation sessions
│   │   └── --home-<user>--/
│   │       └── <timestamp>_<uuid>.jsonl
│   ├── settings.json          # Package manifest, model config
│   ├── auth.json              # OAuth tokens (sensitive!)
│   └── mcp-oauth/             # MCP server auth tokens
├── memory/cortex/             # Vector DB, pattern tracking
│   ├── session-state.json
│   ├── patterns.json
│   └── vectors/
└── cache/                     # Extension caches
```

---

## 1. Prompt History (`~/.claude/history.jsonl`)

### Schema

```json
{
  "display": "actual user prompt text",
  "pastedContents": {
    "1": {
      "id": 1,
      "type": "text",
      "content": "pasted text content",
      "contentHash": "a5d6f8a6c89536a2"  // For large pastes
    }
  },
  "project": "/home/<user>/Developer/project",
  "sessionId": "e6a5f64f-44e3-4acd-a7f4-44a89f641e90",
  "timestamp": 1769876689228
}
```

### Characteristics

| Attribute | Value |
|-----------|-------|
 **Format** | JSON Lines (one JSON object per line)
 **Token counts** | ❌ None
 **Usage data** | ❌ None
 **Sensitive data** | ⚠️ Raw prompts (may contain pasted secrets)
 **Size** | Grows indefinitely (918KB+ in sample)

### Security Note

This file contains **raw prompt text** including anything you paste:
- API keys
- Credentials
- Internal URLs
- Employee IDs

**Risk Level:** 🔴 HIGH — No access controls, plain text storage

---

## Data Sanitization Notes

> **All examples in this document use placeholder values:**
> - `<user>` — Replaces actual Unix username
> - `<company>` — Replaces organization name
> - `<company-provider>` — Replaces internal AI model provider
> - `<internal-system>` / `<internal-service>` — Replaces internal infrastructure references
> - `<jwt-token>`, `<refresh-token-value>` — Replace actual token values
> - `<git-host>` — Replaces internal Git hostnames
> - `<employee-id>` — Replaces employee identifier patterns
> 
> **Real paths will vary by installation.**

---

## 2. Project Sessions (`~/.claude/projects/<project-path>/*.jsonl`)

### Schema

#### User Message Entry

```json
{
  "type": "user",
  "message": {
    "role": "user",
    "content": [
      {
        "type": "text",
        "text": "user prompt here"
      }
    ]
  },
  "uuid": "ac00955f-cc45-46cb-9ad4-899b941bf375",
  "timestamp": "2026-04-08T15:42:19.721Z",
  "sessionId": "2ec4798d-ab34-4955-a79d-8877f6e9d605",
  "version": "2.1.94",
  "cwd": "/home/<user>/Developer/project",
  "gitBranch": "main"
}
```

#### Assistant Message Entry

```json
{
  "type": "assistant",
  "message": {
    "model": "claude-haiku-4-5-20251001",
    "role": "assistant",
    "content": [
      {
        "type": "text",
        "text": "assistant response"
      }
    ],
    "usage": {
      "input_tokens": 2188,
      "output_tokens": 113,
      "cache_creation_input_tokens": 0,
      "cache_read_input_tokens": 0,
      "cache_creation": {
        "ephemeral_5m_input_tokens": 0,
        "ephemeral_1h_input_tokens": 0
      }
    }
  },
  "timestamp": "2026-04-08T15:42:24.533Z",
  "sessionId": "2ec4798d-ab34-4955-a79d-8877f6e9d605"
}
```

#### Queue Operation Entry

```json
{
  "type": "queue-operation",
  "operation": "enqueue",
  "timestamp": "2026-04-08T15:42:19.714Z",
  "sessionId": "2ec4798d-ab34-4955-a79d-8877f6e9d605",
  "content": "CONTEXT:\nAssistant: ...\nCURRENT MESSAGE:\nI have push access to her repo?"
}
```

### Characteristics

| Attribute | Value |
|-----------|-------|
 **Format** | JSON Lines
 **Token counts** | ✅ Yes (in assistant messages only)
 **Usage data** | ⚠️ Partial (tokens, no cost)
 **Context chaining** | ✅ Full conversation context
 **Tool calls** | ✅ Nested in assistant messages
 **Sensitive data** | ⚠️ Full prompt + response history

### Token Usage Schema

```json
{
  "usage": {
    "input_tokens": 2188,
    "output_tokens": 113,
    "cache_creation_input_tokens": 0,
    "cache_read_input_tokens": 0,
    "server_tool_use": {
      "web_search_requests": 0,
      "web_fetch_requests": 0
    },
    "service_tier": "standard",
    "iterations": [],
    "speed": "standard"
  }
}
```

**Cache token categories:**
- `ephemeral_5m_input_tokens` — 5-minute cache window  
- `ephemeral_1h_input_tokens` — 1-hour cache window

---

## 3. Session Registry (`~/.claude/sessions/<pid>.json`)

### Schema

```json
{
  "pid": 121229,
  "sessionId": "a267d3a9-f465-4a0a-adff-fcc4232fdfa1",
  "cwd": "/home/<user>/Developer/shared/project",
  "startedAt": 1775120307776,
  "kind": "interactive",
  "entrypoint": "cli"
}
```

### Characteristics

| Attribute | Value |
|-----------|-------|
 **Purpose** | Map OS process ID to session UUID
 **Token counts** | ❌ None
 **Sensitive data** | ❌ None (metadata only)
 **Use case** | Session management, cleanup

---

## 4. Pi Agent Sessions (`~/.pi/agent/sessions/<workspace>/*.jsonl`)

### Schema

```json
{
  "type": "message",
  "id": "85224c70",
  "parentId": "1ffd4809",
  "timestamp": "2026-04-05T09:04:47.233Z",
  "message": {
    "role": "user",
    "content": [
      {
        "type": "text",
        "text": "user prompt"
      }
    ],
    "timestamp": 1775379885786
  }
}
```

```json
{
  "type": "message",
  "id": "c206dad9",
  "timestamp": "2026-04-05T09:04:55.730Z",
  "message": {
    "role": "assistant",
    "content": [
      {
        "type": "thinking",
        "thinking": "thinking content",
        "thinkingSignature": "reasoning_content"
      },
      {
        "type": "toolCall",
        "toolCallId": "...",
        "toolName": "bash",
        "arguments": {...}
      }
    ],
    "api": "openai-completions",
    "provider": "<company-provider>",
    "model": "claude-sonnet-4-6",
    "usage": {
      "input": 54755,
      "output": 296,
      "totalTokens": 55051,
      "cost": {
        "input": 0,
        "output": 0,
        "total": 0
      }
    }
  }
}
```

### Characteristics

| Attribute | Value |
|-----------|-------|
 **Format** | JSON Lines
 **Token counts** | ✅ Yes (input/output/totalTokens)
 **Cost data** | ✅ Present (often 0 for internal providers)
 **Thinking blocks** | ✅ Separate from tool calls
 **Tool results** | ✅ Separate message type

---

## 5. Authentication Storage

### Pi Auth (`~/.pi/agent/auth.json`)

```json
{
  "<internal-service>": {
    "type": "oauth",
    "refresh": "client_credentials",
    "access": "<jwt-access-token>",
    "expires": 1775669436966
  }
}
```

**Security:** 🔴 **CRITICAL** — Contains live JWT access tokens

### MCP OAuth (`~/.pi/agent/mcp-oauth/<server>/tokens.json`)

```json
{
  "access_token": "<jwt-access-token>",
  "refresh_token": "<refresh-token-value>",
  "token_type": "Bearer",
  "expires_in": 3600,
  "expiresAt": 1775069720845
}
```

**Security:** 🔴 **CRITICAL** — OAuth tokens for internal services

---

## Query Patterns

### Extract Token Usage by Session

```bash
# Claude Code sessions
jq -r 'select(.message.usage) | [
  .timestamp,
  .message.usage.input_tokens,
  .message.usage.output_tokens,
  .message.model
] | @tsv' ~/.claude/projects/<project>/*.jsonl

# Pi sessions
jq -r 'select(.message.usage) | [
  .timestamp,
  .message.usage.input,
  .message.usage.output,
  .message.provider
] | @tsv' ~/.pi/agent/sessions/<workspace>/*.jsonl
```

### Calculate Session Totals

```bash
# Sum all input/output tokens per session
jq -s '{
  input: map(select(.message.usage.input_tokens) | .message.usage.input_tokens) | add,
  output: map(select(.message.usage.output_tokens) | .message.usage.output_tokens) | add
}' ~/.claude/projects/<project>/*.jsonl
```

### Extract User Prompts Only

```bash
# All user prompts (Claude Code)
jq -r 'select(.type=="user") | .message.content[0].text' ~/.claude/projects/<project>/*.jsonl

# All user prompts (Pi)
jq -r 'select(.message.role=="user") | .message.content[0].text' ~/.pi/agent/sessions/<workspace>/*.jsonl

# From history.jsonl
jq -r '.display' ~/.claude/history.jsonl | grep -v "^null$"
```

### Find Sensitive Patterns

```bash
# API keys in prompts
grep -oiE "(AIza[0-9A-Za-z_-]{35,}|sk-[a-zA-Z0-9]{20,}|eyJhbGci[0-9A-Za-z_-]+)" ~/.claude/history.jsonl

# Internal URLs
grep -oiE "https?://[a-z0-9.-]*(<company>|<internal-system>|<git-host>)[a-z0-9.-]*" ~/.claude/projects/*/*.jsonl

# Employee IDs
grep -oE "<employee-id>" ~/.claude/projects/*/*.jsonl
```

---

## Security Classification

| Location | Sensitivity | Contains Secrets? | Rotate If Exposed? |
|----------|-------------|-------------------|-------------------|
| `~/.claude/history.jsonl` | 🔴 **CRITICAL** | ✅ Pasted keys, credentials | N/A (history) |
| `~/.claude/projects/*/*.jsonl` | 🔴 **CRITICAL** | ✅ Full conversation context | N/A (history) |
| `~/.pi/agent/sessions/*/*.jsonl` | 🟡 **HIGH** | ⚠️ Context, some tokens | N/A (history) |
| `~/.pi/agent/auth.json` | 🔴 **CRITICAL** | ✅ Live JWT tokens | ✅ **YES** |
| `~/.pi/agent/mcp-oauth/*/*.json` | 🔴 **CRITICAL** | ✅ OAuth tokens | ✅ **YES** |
| `~/.claude/sessions/*.json` | 🟢 **LOW** | ❌ Metadata only | ❌ No |
| `~/.pi/agent/settings.json` | 🟡 **MEDIUM** | ⚠️ Package list, model config | ❌ No |

---

## Dashboard Integration

### For AI Usage Monitoring (Features 1-4, 6-7)

```python
import json
import glob
from datetime import datetime

def parse_claude_sessions(project_path):
    """Extract usage data from Claude Code sessions."""
    usage_data = []
    
    for filepath in glob.glob(f"{project_path}/*.jsonl"):
        with open(filepath) as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                    if entry.get("type") == "assistant" and entry.get("message", {}).get("usage"):
                        usage = entry["message"]["usage"]
                        usage_data.append({
                            "timestamp": entry["timestamp"],
                            "model": entry["message"]["model"],
                            "input_tokens": usage.get("input_tokens", 0),
                            "output_tokens": usage.get("output_tokens", 0),
                            "cache_read": usage.get("cache_read_input_tokens", 0),
                            "cache_write": usage.get("cache_creation_input_tokens", 0),
                            "session_id": entry.get("sessionId")
                        })
                except json.JSONDecodeError:
                    continue
    
    return usage_data

# Calculate daily aggregates
def aggregate_daily(usage_data):
    daily = {}
    for entry in usage_data:
        day = entry["timestamp"][:10]  # YYYY-MM-DD
        if day not in daily:
            daily[day] = {"input": 0, "output": 0, "sessions": set()}
        daily[day]["input"] += entry["input_tokens"]
        daily[day]["output"] += entry["output_tokens"]
        daily[day]["sessions"].add(entry["session_id"])
    
    return daily
```

### For Critical Prompt Flagging (Feature 11)

```python
import re

CRITICAL_PATTERNS = {
    "google_api_key": r"AIza[0-9A-Za-z_-]{35,}",
    "generic_api_key": r"sk-[a-zA-Z0-9]{20,}",
    "jwt_token": r"eyJhbGci[0-9A-Za-z_-]+\.[0-9A-Za-z_-]+\.[0-9A-Za-z_-]+",
    "aws_access_key": r"ASIA[0-9A-Z]{16,}",
    "aws_secret_key": r"[0-9A-Za-z/+=]{40}",  # After export statement
    "company_proxy": r"https?://[a-z0-9.-]*<company>[a-z0-9.-]*",
    "internal_endpoint": r"https?://[a-z0-9.-]*<internal-system>[a-z0-9.-]*",
    "git_internal": r"<git-host>",
    "employee_id": r"<employee-id>",
    "export_secret": r"export (AWS|SECRET|KEY|TOKEN|PASSWORD)[A-Z_]*=.*"
}

def scan_prompt_for_secrets(prompt_text):
    """Returns list of matched patterns with severity."""
    findings = []
    for pattern_name, pattern in CRITICAL_PATTERNS.items():
        if re.search(pattern, prompt_text, re.IGNORECASE):
            severity = "CRITICAL" if "key" in pattern_name or "token" in pattern_name or "secret" in pattern_name else "HIGH"
            findings.append({
                "pattern": pattern_name,
                "severity": severity,
                "match": re.search(pattern, prompt_text).group()[:50]  # Truncated
            })
    return findings
```

---

## Related Files in This Project

- `../README.md` — Project overview and dashboard features
- `./` — Data model reference (this file)

## External References

- [Claude Code Documentation](https://docs.anthropic.com/en/docs/claude-code)
- [pi-mono Repository](https://github.com/badlogic/pi-mono)
- Claude Code CHANGELOG (local): `~/.pi/mono/packages/coding-agent/CHANGELOG.md`

---

*Last updated: 2026-04-08*
*Generated from analysis of local Claude Code / Pi agent installations*
*Sanitized for general reference use*