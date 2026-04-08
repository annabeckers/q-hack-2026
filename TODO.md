# TODO — Data & Analysis Pipeline

## Docs
- [x] `pipeline.md` — data model, analyzer contract, ops commands
- [x] `concept.md` — product narrative, legal analysis, business model
- [x] `evaluation_output.md` — gap analysis with priority rankings
- [x] `data-model.md` — updated with chats, findings, materialized views
- [x] `architecture.md` — updated with analysis pipeline diagram + analyzer registry
- [x] `API/ENDPOINT_QUICK_REFERENCE.md` — corrected status of trends/alerts endpoints

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
- [x] **Wired into `run_analysis_worker.py`** via `deterministic_extraction.py`
- [x] Secrets scanner (API keys, tokens, passwords, connection strings, private keys)
- [x] PII scanner (emails, IPs, phone numbers, internal paths)
- [x] Slopsquatting scanner (hallucinated packages in install/import statements)
- [ ] Financial data detection (contract values, salary data from company tables)
- [ ] Registry lookup for slopsquatting (verify packages against PyPI/npm)

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
- [x] `run_analysis_worker.py` — loop mode, both deterministic + LLM wired
- [x] Materialized view refresh after analysis
- [x] Deterministic analyzers wired into worker
- [x] End-to-end pipeline: import → deterministic → LLM → refresh views
- [ ] Add `google-genai` to docker image (added to pyproject.toml)
