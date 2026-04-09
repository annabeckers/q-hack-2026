# Argus — AI Usage Intelligence

## Your developers are leaking secrets to AI — and nobody is watching.

Real-time secret detection. Malicious package scanning. Cost and compliance visibility.
Deployed on a Raspberry Pi you ship to any team — no cloud required, working in minutes.

> Full concept: [concept.md](docs/concept.md) | Architecture: [architecture.md](docs/architecture.md) | Pipeline: [docs/pipeline.md](docs/pipeline.md) | Data model: [data-model.md](docs/data-model.md)

---

## Core Idea

Argus enables companies to **govern their AI usage** and detect **data integrity leaks** before they become incidents. As enterprises rapidly adopt AI tools across departments, they lose visibility into what sensitive data is being shared with external models, which malicious packages AI might be hallucinating into install commands, and how costs are spiraling without attribution. Argus provides a centralized intelligence layer that monitors, analyzes, and secures all AI interactions — from ChatGPT conversations to Claude Code sessions. By maintaining a complete audit trail with pseudonymized attribution, companies can **stay compliant with emerging AI laws** (EU AI Act) and demonstrate regulatory readiness through a purpose-built overview tool. The platform runs entirely on-premise or on a Raspberry Pi, ensuring zero data egress while delivering enterprise-grade security insights.

---

## Architecture

```mermaid
flowchart TB
    subgraph "Data Sources"
        CHAT[Chat Exports<br/>ChatGPT, Claude, Gemini, Pi]
        JSONL[JSONL Logs<br/>IDE integrations]
        FILES[File Drops<br/>Markdown, JSON]
    end

    subgraph "Ingestion Layer"
        IMPORT[Chat Import Service<br/>6+ format parsers]
        CHATS[(chats table<br/>PostgreSQL)]
    end

    subgraph "Analysis Pipeline"
        WORKER[Analysis Worker<br/>Polls every 15-30s]
        
        subgraph "Deterministic Analyzers"
            SECRETS[Secrets Scanner<br/>API keys, tokens, passwords]
            PII[PII Detector<br/>Emails, IPs, IBANs]
            SLOP[Slopsquatting Detector<br/>Hallucinated packages]
        end
        
        subgraph "LLM Analyzers"
            TRIVIAL[Trivial Usage<br/>Productive vs wasteful]
            SENSITIVITY[Sensitivity Analysis<br/>Business-critical content]
            COMPLEXITY[Complexity Scoring<br/>1-10 scale]
        end
        
        META[Meta Analyzer<br/>Risk aggregation]
        REC[Recommender Agent<br/>Security/Cost advice]
    end

    subgraph "Storage Layer"
        FINDINGS[(findings table<br/>PostgreSQL)]
        VIEWS[Materialized Views<br/>Pre-computed aggregates]
        NEO4J[(Neo4j<br/>Knowledge graphs)]
        REDIS[(Redis<br/>Cache + Sessions)]
    end

    subgraph "API Layer"
        FASTAPI[FastAPI<br/>:8000]
        DASHBOARD_API[Dashboard Endpoints]
        AGENTS_API[Agent Endpoints<br/>5 frameworks]
    end

    subgraph "Frontend"
        REACT[React + Vite + Tailwind<br/>:3000]
        DASHBOARD[Command Center<br/>Real-time monitoring]
        COMPLIANCE[Compliance Dashboard<br/>EU AI Act readiness]
    end

    CHAT --> IMPORT
    JSONL --> IMPORT
    FILES --> IMPORT
    IMPORT --> CHATS
    
    CHATS --> WORKER
    WORKER --> SECRETS
    WORKER --> PII
    WORKER --> SLOP
    WORKER --> TRIVIAL
    WORKER --> SENSITIVITY
    WORKER --> COMPLEXITY
    
    SECRETS --> FINDINGS
    PII --> FINDINGS
    SLOP --> FINDINGS
    TRIVIAL --> FINDINGS
    SENSITIVITY --> FINDINGS
    COMPLEXITY --> FINDINGS
    
    FINDINGS --> META
    META --> REC
    REC --> VIEWS
    
    FINDINGS --> VIEWS
    CHATS --> VIEWS
    
    VIEWS --> DASHBOARD_API
    FINDINGS --> DASHBOARD_API
    
    DASHBOARD_API --> FASTAPI
    AGENTS_API --> FASTAPI
    
    FASTAPI --> REACT
    REACT --> DASHBOARD
    REACT --> COMPLIANCE
    
    FASTAPI <--> NEO4J
    FASTAPI <--> REDIS
```

---

## Quickstart

```bash
# 1. Create .env
cp .env.example .env
# → Add GOOGLE_API_KEY for LLM analysis

# 2. Start the stack (backend + frontend + postgres + redis)
docker compose up -d

# 3. Seed demo data
task seed-database
task import-chats

# 4. Open
# Frontend:  http://localhost:3000
# API docs:  http://localhost:8000/docs
```

### Useful commands

```bash
task up              # Start services
task down            # Stop services
task logs            # Tail logs
task test            # Run backend tests
task lint            # Lint backend
task nuke            # Stop + delete all volumes
```

---

## Stack

| Component | Tech | Port |
|-----------|------|------|
| **Backend** | FastAPI + Python 3.12 (uv) | `:8000` |
| **Worker** | Analysis pipeline (same image, sidecar) | — |
| **Frontend** | React + Vite + TailwindCSS | `:3000` |
| **Database** | PostgreSQL 16 | `:5432` |
| **LLM** | Gemini Flash (switchable via `MODEL_PROVIDER`) | — |

### Optional services

```bash
# Neo4j, ChromaDB, Rust worker
docker compose --profile extras up -d

# Observability (Jaeger, Prometheus, Grafana)
docker compose --profile observability up -d
```

---

## What It Does

1. **Import** — Ingests AI chat exports (ChatGPT, Gemini, Claude, Pi, AntiGravity)
2. **Scan** — Deterministic regex: secrets, PII, slopsquatting
3. **Analyze** — LLM analysis: trivial usage, sensitivity, complexity scoring
4. **Dashboard** — Materialized views → fast API endpoints → React frontend
5. **Agent** — Gemini-powered agent with tools to query findings in natural language

---

## Security & DSGVO

- No real user data in demo — all hashed/pseudonymized
- Secrets scanner runs on local LLMs too (on-device)
- LLM prompts use only anonymized aggregate data
- Audit-logging structured for EU AI Act compliance
