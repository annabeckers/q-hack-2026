# Concept — AI Usage Intelligence Platform

## Problem

Enterprises have no visibility into how AI tools are used across their organization. Developers paste secrets into prompts. AI assistants recommend malicious packages. Costs spiral without attribution. Compliance teams can't audit what they can't see — and regulators (EU AI Act) are about to start asking.

## Solution

An intelligence layer that monitors, analyzes, and secures enterprise AI usage. Deployed as a **Raspberry Pi plug-and-play test lab** — zero cloud dependency, working in minutes.

## Core Features

### 1. Real-Time Secret Detection (Key Feature)
- Scans every outgoing prompt for API keys, AWS secrets, passwords, internal IPs, PII
- Regex + entropy-based detection — no LLM in the hot path, minimal latency
- Instant alert: dashboard flag (red sidebar), Slack/email/webhook notification
- Auto-notification to source: "API key detected — rotate immediately"

### 2. Slopsquatting Detection (Novel)
- AI systems recommend non-existent or typosquatted package names
- Scanner checks AI-generated `import` statements against PyPI/npm registries
- Flags unknown, suspicious, or recently-created packages
- Prevents supply chain attacks before code is committed

### 3. Cost & Usage Analytics
- Track which AI tools, models, and providers are used across departments
- Cost attribution: department → team → user (pseudonymized)
- Model comparison: cost/quality ratio, cheaper alternative recommendations
- Budget alerts and trend analysis

### 4. Provider Data Flow Mapping
- Which agents access which codebases?
- Do they index the full repository? (IP risk)
- Mapping: data type → provider → region → privacy risk level

### 5. Sentiment Analysis (Aggregate Only)
- Company-wide and department-level sentiment trends in AI interactions
- Aggregated and anonymized — no individual-level tracking
- Detects frustration patterns, adoption barriers, training needs
- Legal: GDPR Art. 6(1)(f) compliant when aggregate-only, requires Betriebsrat sign-off

### 6. EU AI Act Compliance Readiness
- Track which models may be classified "high risk"
- Structured audit trail: purpose, model, region, timestamp
- Preparation for upcoming reporting obligations
- Self-awareness: the dashboard itself may need compliance documentation

## Data Collection Methods

Three approaches depending on the target:
1. **Local file analysis** — Parse conversation logs from agentic IDEs (Claude Code, Cursor, Pi Agent, etc.)
2. **OpenTelemetry** — For software that supports it natively
3. **Network-level analysis** — Traffic inspection on the Pi device for web-based AI interfaces

## Deployment Model — Raspberry Pi Test Lab

**Not a proxy. A self-contained playground.**

The Pi is shipped preconfigured to companies as a standalone test environment:
- Plug in, connect to network, service starts automatically
- Runs the full analysis stack: secret scanning, slopsquatting, cost tracking
- Live dashboard accessible via browser on local network
- Local LLM available for on-device classification (lightweight models only)
- After test phase: generates a comprehensive report with findings and recommendations
- Report serves as basis for full-service engagement (upselling)

**Alternative deployment:** Pi as a server within existing infrastructure for teams that want persistent monitoring.

## Business Model

| Tier | Offering | Target |
|------|----------|--------|
| Free / Low-Cost | General dashboard features, open-source scanners | Universities, small teams |
| Pi Test Lab | Preconfigured hardware shipped for trial period | Mid-market, government |
| Full Service | On-prem deployment, custom rules, integrations, support | Enterprise, regulated industries |

**Go-to-market:** Governments, universities, regulated industries (finance, healthcare, defense). The Pi test lab is the Trojan horse — low commitment entry point that generates data proving the value of the full platform.

## Competitive Landscape

| Competitor | Focus | Our Differentiator |
|------------|-------|-------------------|
| Lakera | Prompt security (SaaS) | We're local-first, no cloud dependency |
| Prompt Security | AI firewall | We add slopsquatting + cost analytics |
| Portkey | LLM observability | We focus on security, not just metrics |
| Galileo | Model monitoring | We're deployment-agnostic, Pi-based |

**Core differentiator:** Local-first, zero-trust architecture. Your data never leaves your network. The Pi proves it.

## Legal Considerations

- **Feature 7 from original scope (private usage detection) — DROPPED.** BetrVG §87(1) Nr. 6 makes individual-level usage classification a works council co-determination issue. Legal minefield in Germany.
- **Sentiment analysis — OK if aggregate-only.** Department-level trends without individual attribution. Requires Betriebsrat notification in most German companies.
- **Secret scanning — clearly legitimate.** Security tooling falls under employer's duty to protect infrastructure.
- **GDPR:** All user identifiers hashed. No PII in logs. Audit trail for data access.

## References

- [Antigravity conversation decoder](https://github.com/JonDickson20/antigrav-recovery/blob/master/recover.py) — Potential integration for recovering AI conversation data
- [Scaleway AI](https://www.scaleway.com/en/) — GDPR-compliant EU alternative provider recommendation
