# Dashboard Evaluation — AI Usage Intelligence Platform
> Generated 2026-04-08. Critical analysis of planned frontend features + brainstorm of gaps.

---

## Proposed Frontend Items — Status

| Item | Status | Verdict |
|---|---|---|
| **Costs** | ✅ Solid | `dashboard_aggregator.py` has cost by model/dept/tool |
| **Model usage (message counts)** | ✅ Solid | Already aggregated |
| **Leaks: Security + Content (count per type)** | ⚠️ Miscategorized | See section below |
| **Content / Insights Summary (text)** | ❌ Weak | Unstructured text is unactionable on a dashboard |
| **Libraries (malicious) table** | ✅ Solid | `slopsquatting_scanner.py` covers this |
| **Scatter plot (Complexity vs Leak)** | ⚠️ Undefined | "Fragenkomplexität" isn't computed anywhere in the codebase |

---

## Critical Issue: Leak Taxonomy is Wrong

The codebase already models **three distinct finding types**, but the dashboard collapses them into two:

```
SecretCandidate    → API keys, tokens, DB credentials       → Security leaks
PIICandidate       → emails, names, internal IPs, projects  → Content / data leaks
SlopquatCandidate  → hallucinated packages                  → Supply chain risk  ← missing from taxonomy
```

Calling it "Security Leaks / Content Leaks" loses slopsquatting entirely. More importantly, `secrets_scanner.py` already has `critical / high / medium` severity — that axis is more operationally useful than the category split. A CISO cares about "3 critical, 12 high" more than "15 security leaks."

**Fix:** Show three categories. Within each, break down by severity (critical / high / medium), not just count.

---

## Slopsquatting by LLM Model

The `SlopquatCandidate` data model has `provider` on every finding and `suggestedByAI: boolean`. This enables a directly computable chart:

> "How many hallucinated / malicious packages were suggested per AI model?"

This is more defensible and technically accurate than comparing credential leaks across providers (which is influenced by usage volume, not model quality). A bar chart here — `chatgpt-4o: 34 hallucinated, gemini-2.0-flash: 22, claude-opus-4-6: 8` — is a concrete security signal that differentiates models by their hallucination rate in code generation.

Also track: hallucination type breakdown per model — packages vs fabricated API endpoints vs fabricated CLI tools vs fabricated RBAC roles. The `chat-history-data-model.md` already distinguishes these three subtypes.

---

## What's Missing (Standard Gaps)

**1. Severity distribution for leaks**
"23 leaks" is meaningless. "3 critical (production DB creds, AWS keys), 8 high, 12 medium" is actionable. The data is there in `secrets_scanner.py`, the frontend doesn't surface it.

**2. Department attribution**
`by_dept` is in the aggregator. "Engineering generates 80% of costs but 90% of leaks" is the insight that gets you the meeting with the CISO. Not in the frontend spec.

**3. EU AI Act Compliance Score**
Already computed in `dashboard_aggregator.py` via `legislation_score()`. Checks: purpose logged, region logged, model name, department, user pseudonymization. It's your only differentiator against Lakera/Portkey and directly addresses the regulatory fear driving enterprise purchase decisions. Should be a prominent gauge on the main view.

**4. Time-series / trend view**
Everything is currently a static snapshot. "Leaks per week", "did the new AI policy reduce incidents?", cost trend month-over-month — without a time axis this looks like a one-time audit tool, not monitoring infrastructure. The DB schema already has `usage_start` indexed for this.

**5. Real-time alert feed**
`concept.md` specifies "red sidebar flag, instant alert." Not in the frontend spec. For the hackathon demo this is the WOW moment: live stream of leaks appearing as they're detected. Even mocked with the existing `flagged_secrets.jsonl` polling it works.

**6. Drill-down / conversation explorer**
You can see a count of leaks — then what? "Show me the conversation where the AWS key leaked, with surrounding context" is table stakes for security tooling. The `matchContext` field (±200 chars) in `SecretCandidate` already supports this. Without drill-down, analysts can't act.

**7. Recommendation panel**
`concept.md` mentions "cheaper alternative recommendations" and "model comparison: cost/quality ratio." Not in frontend. A simple callout: "40% of your spend is on trivial Q&A — equivalent Mistral 7B cost would save €X/month" closes the loop from diagnosis to action.

---

## What's Missing (Outside the Box)

**8. Context window accumulation risk score**
In agentic sessions (Claude Code, Pi Agent), the AI reads files into context on every tool call. The longer the session, the more sensitive files accumulate in the context window that gets transmitted to the external API. A user who ran a 200-turn session that accessed `.env`, `config.yaml`, and `secrets.json` represents a fundamentally different risk than a 3-turn Q&A session — even if no hard-coded secret regex matched.

The data is in `ToolInvocation.filesAccessed`. A "context exposure score" = weighted sum of sensitive file types read per session. Show top 10 riskiest sessions. This is a novel insight no existing tool surfaces.

**9. File type exposure heatmap**
Which file types are being read into AI context across all sessions? A heatmap of `filesAccessed` extensions: `.env`, `.pem`, `.p12`, `config.yaml`, `docker-compose.yml`, `.sql` should be automatic red flags. Cross this with department to get: "DevOps team is sending private key files to AI providers 3x per week."

**10. Prompt injection detection**
Everything so far is about data flowing OUT (leaks). Prompt injection is attacks coming IN — the AI receives malicious instructions embedded in tool outputs, websites fetched, or documents summarized, then executes them in your environment. Signals: instructions in unusual positions (tool result containing "ignore previous instructions"), unusual command sequences immediately after a web fetch or file read. A separate "Attack Surface" panel distinct from the leak panels would be distinctive.

**11. Cross-user duplicate secret detection**
If the same AWS key appears in conversations from 3 different anonymized users, that's a shared production credential being leaked repeatedly by multiple employees — a systemic problem, not an individual incident. After anonymization, a hash of the secret value (not the secret itself) enables cross-correlation. "This credential appeared in 5 separate sessions" is a different severity than "this credential appeared once."

**12. Shadow AI detection**
The corporate policy might be "only use Microsoft Copilot" but conversations from ChatGPT, Claude, and Gemini show up in the logs. A "Approved vs Unapproved Providers" split based on a configurable allowlist surfaces shadow AI usage without any network-level interception. If `tool_name` or `provider` isn't in the approved list, it's flagged automatically.

**13. Behavioral anomaly alerts**
Establish a statistical baseline per department (rolling 30-day average: cost, token count, leak rate). Alert when a department's current week deviates by >2σ. "Dept X's AI cost spiked 400% this week" could be a new project or someone running automated AI scripts against company budget. Z-score detection is implementable with the existing `daily_department_summary` view.

**14. Time-of-day risk pattern**
When are the riskiest sessions happening? If 80% of critical leaks occur after 19:00, that implies developers working alone in the evening and copy-pasting from production systems without a review layer active. A heatmap of leak events by hour-of-day vs day-of-week would reveal behavioral patterns that policy can address.

**15. Remediation tracking / alert lifecycle**
When a critical finding is detected, what happened? Open → Acknowledged → Resolved. A status column on the findings table makes this feel like a real security operations tool, not just a scanner. Without remediation tracking, you can't prove to an auditor that findings were acted on — which is exactly the EU AI Act audit trail requirement.

**16. Data flow Sankey diagram**
Visualize: Department → AI Tool → Model → Provider → Provider Region. Show token volume as flow width. Immediately answers: "Are German employees sending data to US-based providers without a DPA?" and "Which department generates the most cross-border data flow?" The `region` field is already in the schema (`step3_schema.sql`) but unused in the frontend.

**17. Conversation archival risk by provider**
Different providers retain conversation data for different periods (OpenAI: 30 days default, some providers: indefinitely). If a user sent internal project details to a provider with no data processing agreement and 180-day retention, that's a GDPR Art. 28 violation in progress. A "retention risk" indicator per provider in the model usage table — populated from a static config — surfaces this without any API calls.

---

## Fix the Scatter Plot Spec

"Fragenkomplexität" doesn't exist in the codebase. Define it explicitly:

- **X-axis:** `token_count` (input tokens, already logged) — best available proxy for query complexity
- **Y-axis:** number of leaks/findings detected per conversation (aggregated from `SecretCandidate` + `PIICandidate`)
- **Each point:** one conversation session
- **Color:** provider (Claude Code / ChatGPT / Gemini / Pi Agent)
- **Size:** session cost (bubble chart variant)

**Insight this reveals:** "Complex coding sessions (high token count, many tool calls) are your highest-risk leak surface." This is defensible, computable, and non-obvious — it tells enterprises where to focus policy controls.

---

## Priority Additions (Ranked)

| Priority | Addition | Data Available? |
|---|---|---|
| 🔴 1 | Severity distribution (critical/high/medium) for all finding types | Yes — `secrets_scanner.py` |
| 🔴 2 | Slopsquatting rate by LLM model | Yes — `SlopquatCandidate.provider` |
| 🔴 3 | EU AI Act compliance gauge | Yes — `legislation_score()` in aggregator |
| 🟡 4 | Time-series / trend sparklines | Yes — `usage_start` indexed in DB |
| 🟡 5 | Department attribution panel | Yes — `by_dept` in aggregator |
| 🟡 6 | Context window accumulation risk (top 10 sessions) | Yes — `filesAccessed` in ToolInvocation |
| 🟡 7 | Real-time alert feed | Yes — poll `flagged_secrets.jsonl` |
| 🟡 8 | Data flow Sankey (dept → tool → model → region) | Yes — `region` field in schema |
| 🟢 9 | Cross-user duplicate secret detection | Requires hashing step on match values |
| 🟢 10 | Drill-down conversation explorer | Yes — `matchContext` in SecretCandidate |
| 🟢 11 | Remediation tracking (open/ack/resolved) | Needs new DB table |
| 🟢 12 | Time-of-day risk heatmap | Yes — `usage_start` |
| 🟢 13 | Shadow AI detection | Yes — compare `tool_name` to allowlist |
| 🟢 14 | Behavioral anomaly alerts | Yes — `daily_department_summary` view |
| 🔵 15 | Prompt injection detection | Partial — needs pattern library |

---

## What to Simplify or Cut

**"Content / Insights Summary (text)"** — as a blob of LLM-generated prose, this doesn't belong on a dashboard. Replace with a structured **Top Entities panel**: top-N project names mentioned, external domains referenced, technologies discussed. Specific > vague.

**Slopsquatting table** — valuable but secondary. Move to a dedicated tab. The primary story is data leakage; slopsquatting is supporting evidence. Don't let it compete for main-view real estate.

**"Low-value / trivial-question detection"** (currently in `dashboard_aggregator.py`) — interesting for ROI conversations with managers, but the detection heuristics (keyword matching on purpose field) are too fragile to surface prominently without false positives embarrassing the demo.
