# ARGUS — AI Usage Intelligence Platform
## Governing AI adoption — before liability hits.

[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Compliance](https://img.shields.io/badge/Compliance-EU_AI_Act-orange.svg)](#-eu-ai-act-readiness)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-6-646CFF?logo=vite&logoColor=white)](https://vitejs.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript&logoColor=white)](https://typescriptlang.org)
[![Bun](https://img.shields.io/badge/Bun-1.x-000000?logo=bun&logoColor=white)](https://bun.sh)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://docker.com)


---

### 🛡️ The Mission
**Your employees are using ChatGPT, Claude, and Gemini every day.** They're pasting source code, customer data, and internal documents. That data is leaving your company right now, without visibility and without control.

This isn't a hypothetical. This is reality. Leaked secrets, hallucinated packages entering your codebase, and spiraling costs. **ARGUS makes all of this visible.** We help companies govern AI adoption before it becomes a liability.

---

### 🚀 Key Capabilities

| Feature | Description |
| :--- | :--- |
| **Critical Findings** | Real-time detection of leaked AWS keys, PII (emails, IPs, IBANs), and database credentials. |
| **Slopsquatting Scan** | Detect hallucinated or malicious packages (e.g., `reqests`, `pandass`) suggested by AI. |
| **Provider-Agnostic** | One dashboard for all tools. Monitor OpenAI, Anthropic, Gemini, and local Ollama models. |
| **Compliance Score** | Automated audit trails and risk documentation ready for the **EU AI Act**. |
| **Cost Intelligence** | Aggregate spend by department and model with recommendations for 40%+ cost savings. |

---

### 📦 The "Ready-to-Go" Lab Device
We focus on **data integrity**. Once your data leaves your network, you've lost control. We ship ARGUS as a ready-to-go lab device (or on-prem software) that proves your risk exposure.

- **Deterministic & Agentic**: Combines high-speed regex scanning with LLM-powered sensitivity analysis.
- **Edge Deployment**: Runs entirely inside your walls on affordable hardware like a Raspberry Pi.

---

### 🛠️ Architecture

```mermaid
flowchart TB
    subgraph "Data Sources (Live & Batch)"
        PROXY[Live Proxy / API]
        CHAT[Chat Exports<br/>ChatGPT, Claude, Gemini]
        JSONL[JSONL Logs<br/>IDE / CLI logs]
    end

    subgraph "Analysis Pipeline"
        WORKER[Analysis Worker]
        
        subgraph "Deterministic Analyzers"
            SECRETS[Secrets Scanner<br/>API keys, tokens]
            PII[PII Detector<br/>Emails, IPs, IBANs]
            SLOP[Slopsquatting Detector<br/>Hallucinated packages]
        end
        
        subgraph "Agentic Analyzers (LLM)"
            SENSITIVITY[Sensitivity Analysis]
            QUALITY[Usage Quality Scan]
            COMPLIANCE[EU AI Act Scoring]
        end
    end

    subgraph "Storage & Intelligence"
        PG[(PostgreSQL<br/>Audit Trails)]
        VIEWS[Materialized Views<br/>Risk Aggregates]
        REC[Recommender Agent<br/>Cost/Security Advice]
    end

    subgraph "Command Center"
        FASTAPI[FastAPI Backend]
        REACT[React Dashboard]
    end

    PROXY --> WORKER
    CHAT --> WORKER
    JSONL --> WORKER
    
    WORKER --> SECRETS & PII & SLOP
    WORKER --> SENSITIVITY & QUALITY & COMPLIANCE
    
    SECRETS & PII & SLOP --> PG
    SENSITIVITY & QUALITY & COMPLIANCE --> PG
    
    PG --> VIEWS
    VIEWS --> REC
    REC --> VIEWS
    
    VIEWS --> FASTAPI
    FASTAPI --> REACT
```

---

### 🏁 Quickstart for Judges
Follow these steps to launch the ARGUS production environment.

1.  **Ensure Docker is installed** and the domain/TLS is configured (for production).
2.  **Setup Environment**:
    ```bash
    cp .env.example .env
    # Edit .env and populate GOOGLE_API_KEY
    ```
3.  **Start Platform**:
    ```bash
    docker compose up -d
    ```


**Access URLs:**
- **Frontend Command Center**: `http://localhost:3000`

---