# TODO — Argus: AI Usage Intelligence

## Completed ✅

### Docs
- [x] `pipeline.md` — data model, analyzer contract, ops commands, materialized views rationale
- [x] `concept.md` — product narrative, legal analysis, business model
- [x] `data-model.md` — chats, findings, materialized views, deterministic tables
- [x] `architecture.md` — analysis pipeline diagram + analyzer registry
- [x] `README.md` — quickstart, stack overview, model switching

### Data Pipeline
- [x] Chat import — 6+ formats (ChatGPT, Gemini, Wildchat, Claude, Pi, AntiGravity)
- [x] Text cleaning & PII/secret redaction (regex)
- [x] Deduplication via SHA256 hash
- [x] Schema: chats, findings, deterministic tables (001-003)
- [x] Materialized views for dashboard (004)

### Deterministic Analysis
- [x] Regex matching against company data rules
- [x] Rule auto-generation from employees/customers/documents tables
- [x] Secrets scanner (API keys, tokens, passwords, connection strings)
- [x] PII scanner (emails, IPs, phone numbers, internal paths)
- [x] Slopsquatting scanner (hallucinated packages in install/import)

### LLM Analysis
- [x] Gemini Flash integration — 3 analyzers (trivial, sensitivity, complexity)
- [x] Batch processing with idempotent skip
- [x] Findings persistence to DB

### Agent
- [x] Strands SDK agent with switchable model provider (Gemini/Ollama/OpenAI)
- [x] 5 `@tool` decorated analysis tools (findings, risk, secrets, stats, overview)
- [x] `/api/v1/agents/invoke` endpoint

### Worker
- [x] `run_analysis_worker.py` — loop mode, deterministic + LLM, view refresh
- [x] Docker sidecar with health check + graceful shutdown
- [x] End-to-end: import → deterministic → LLM → refresh views → dashboard

### API
- [x] 23 dashboard endpoints wired
- [x] Auth router

---

## Next Up 🔲

### Frontend
- [ ] Connect dashboard to real API endpoints
- [ ] Agent chat UI (hit `/api/v1/agents/invoke`)
- [ ] Verify frontend renders data from materialized views

### Demo Data
- [ ] Seed company reference data (employees, customers, documents) for demo
- [ ] Auto-import chat exports on first boot

### Analysis Improvements
- [ ] Financial data detection (contract values, salary data)
- [ ] Registry lookup for slopsquatting (verify against PyPI/npm)
- [ ] Add retry logic on LLM API failure
- [ ] Parallel analyzer invocation (currently sequential)

### LLM Insights Layer
- [ ] Meta-analyzer — reason across deterministic + LLM findings
- [ ] Flag high-risk conversations (high secrets + high complexity)
- [ ] Per-department risk scoring
- [ ] Content/Insights summary per conversation

### Recommendations
- [ ] Engine logic — provider recs based on risk/cost/compliance
- [ ] Alternative model suggestions (cheaper/safer for simple tasks)
- [ ] Training recommendations based on leak patterns
- [ ] API endpoint (`GET /api/v1/recommendations`)

### Polish
- [ ] Export findings as CSV/PDF
- [ ] Content summary endpoint