# API Endpoints Quick Reference

> For full details, see `openapi.yaml` / `openapi.json`



## Analytics Endpoints

| Endpoint | Method | Purpose | Params |
|----------|--------|---------|--------|
| `/summary/compliance-gauge` | GET | EU AI Act compliance score (0-100) |  |
| `/analytics/cost` | GET | Session-first cost analytics, then grouped by dimension | `dimension`, `cost_basis=per_session`, `limit`, `startDate`, `endDate` |
| `/analytics/usage` | GET | Average usage per session, usage defined as average word count | `dimension`, `metric=avgWordCountPerSession`, `startDate`, `endDate` |
| `/analytics/model-comparison` | GET | Model metrics: cost/token, leak rate, hallucination rate | `department` |



## Security — Findings Endpoints

| Endpoint | Method | Purpose | Params |
|----------|--------|---------|--------|
| `/security/findings` | GET | All findings (paginated, filterable) | `type`, `severity`, `status`, `department`, `provider`, `limit`, `offset` |
| `/security/findings/{id}` | GET | Single finding with full context | — |
| `/security/leak-counts` | GET | Count of leaks grouped by model and category | `model`, `category` |
| `/security/severity-distribution` | GET | Counts by severity (critical/high/med) per leak type | `department`, `provider` |
| `/security/slopsquatting` | GET | Hallucination rate per dimension | `dimension`, `sortBy` |
| `/security/duplicate-secrets` | GET | Credentials leaked by multiple users | `minUsers` |



---

## Trends Endpoints

| Endpoint | Method | Purpose | Params |
|----------|--------|---------|--------|
| `/trends/timeseries` | GET | Cost/findings over time | `metric`, `granularity`, `department`, `startDate`, `endDate` |
| `/trends/anomalies` | GET | Z-score alerts (>2σ deviation) | `department`, `zscore` |
| `/trends/patterns-by-time` | GET | Risk heatmap (hour-of-day × day-of-week) | — |
| `/trends/complexity-scatter` | GET | Scatter plot data: tokens × findings | `department`, `provider` |



---

## Alerts Endpoints

| Endpoint | Method | Purpose | Params |
|----------|--------|---------|--------|
| `/alerts` | GET | Recent findings feed | `since`, `severity`, `type`, `limit` |
| `/alerts/stream` | GET | Real-time SSE stream | `severity` |
| `/alerts/{id}/acknowledge` | POST | Mark alert as acknowledged | request body: `notes` |



---

## Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad request (invalid params) |
| 404 | Not found |
| 500 | Server error |

All errors include `detail` field with error message.

---

## Common Filters

Most endpoints support:

- **`department`** — Filter by department name
- **`provider`** — Filter by LLM provider (OpenAI, Anthropic, Google, etc.)
- **`startDate`** — ISO 8601 start time
- **`endDate`** — ISO 8601 end time
- **`limit`** — Result count (default varies)
- **`offset`** — Pagination offset (default 0)

---

## Pagination Example

```bash
# Page 1 (50 items)
GET /security/findings?limit=50&offset=0

# Page 2
GET /security/findings?limit=50&offset=50

# Page 3
GET /security/findings?limit=50&offset=100

# Response includes:
# { items: [...], total: 523, offset: 100, limit: 50 }
```

---

## P0 Features (MVP — Hackathon Demo)

| Feature | Endpoint(s) |
|---------|-----------|
| Cost overview | `/analytics/cost?dimension=department&cost_basis=per_session` |
| Usage volume | `/analytics/usage?dimension=model&metric=avgWordCountPerSession` |
| Finding severity | `/security/severity-distribution` |
| Compliance score | `/summary/compliance-gauge` |
| Model comparison | `/analytics/model-comparison` |
| Findings table | `/security/findings` |

---

## P1 Features (Post-MVP)

| Feature | Endpoint(s) |
|---------|-----------|
| Real-time alerts | `/alerts/stream` (SSE) |
| Context risk | `/security/context-risk` |
| Scatter plot | `/explorer/complexity-scatter` |
| Department metrics | `/analytics/department` |
| Time-series trend | `/trends/timeseries` |
| Anomaly detection | `/trends/anomalies` |

---

## P2/P3 Features (Advanced)

| Feature | Endpoint(s) |
|---------|-----------|
| Conversation explorer | `/explorer/conversations/{id}` |
| Audit trail | `/compliance/audit-trail` |
| Data flow (Sankey) | `/compliance/data-flow` |
| Shadow AI detection | `/explorer/shadow-ai` |
| File exposure heatmap | `/security/file-exposure` |
| Duplicate secrets | `/security/duplicate-secrets` |

---
