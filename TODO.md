# TODO — Data & Analysis Pipeline

## Data Preprocessing
- [x] Chat import — 6+ formats (ChatGPT, Gemini, Wildchat, Claude, Pi, AntiGravity)
- [x] Text cleaning & PII/secret redaction (regex)
- [x] Deduplication via SHA256 hash
- [ ] Wire chat import into docker-compose startup (auto-import on boot)

## Database
- [x] Schema: chats, findings, deterministic tables (001-003)
- [x] Materialized views for dashboard (004)
- [ ] Ensure all 4 SQL scripts run cleanly on fresh Postgres
- [ ] Seed company reference data (employees, customers, documents) for demo

## Deterministic Data Analysis
- [x] Analysis logic — regex matching against company data rules
- [x] Rule auto-generation from employees/customers/documents tables
- [x] Repository + persistence layer
- [ ] **Wire into `run_analysis_worker.py`** (currently skipped with TODO)
- [ ] Secrets scanner (leaked keys, tokens, connection strings)
- [ ] PII scanner (names, emails, phone numbers matched against company DB)
- [ ] Slopsquatting scanner (hallucinated packages — check against real registries)
- [ ] Financial data detection (contract values, salary data from company tables)

## LLM Data Analysis
- [x] Gemini Flash integration — 3 analyzers (trivial, sensitivity, complexity)
- [x] Batch processing with idempotent skip
- [x] Findings persistence to DB
- [ ] **Make agentic** — one tool/hook per analysis type (diagram requirement)
- [ ] Add retry logic on API failure
- [ ] Parallel analyzer invocation (currently sequential)
- [ ] Content/Insights Summary — text summary across all findings per conversation

## LLM Insights / Eval Layer
- [ ] Meta-analyzer that reasons across deterministic + LLM findings
- [ ] Flag high-risk conversations (high secrets + high complexity)
- [ ] Per-department risk scoring
- [ ] Confidence calibration across analyzers

## Recommendation Service ("Adventurous Albatross")
- [ ] Engine logic — provider recommendations based on risk/cost/compliance
- [ ] Critical use cases clustered by department
- [ ] Alternative model suggestions (cheaper/safer for simple tasks)
- [ ] Schulungen (training) recommendations based on leak patterns
- [ ] API endpoint (`GET /api/v1/recommendations`)

## API
- [x] 23 dashboard endpoints wired
- [x] Auth router registered
- [ ] Recommendation endpoint
- [ ] Content/Insights Summary endpoint
- [ ] Export findings as CSV/PDF

## Worker / Orchestration
- [x] `run_analysis_worker.py` — loop mode, LLM wired
- [x] Materialized view refresh after analysis
- [ ] Wire deterministic analyzers into worker
- [ ] End-to-end pipeline: import → deterministic → LLM → refresh views
