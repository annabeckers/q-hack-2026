"""
Provider Data Flow Analyzer (Step 10)

Answers: "Which data goes to which AI provider, and what are the risks?"

For each log entry it:
  - Maps model_name → provider (OpenAI, Anthropic, Google, local, …)
  - Maps provider → data residency region and GDPR risk level
  - Flags entries where sensitive tools send data to non-EU providers
  - Detects agents that may be indexing entire codebases

Usage:
    python provider_flow.py [--file logs.jsonl]
"""

import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

# ---------------------------------------------------------------------------
# ANSI
# ---------------------------------------------------------------------------
RED    = "\033[91m"
YELLOW = "\033[93m"
GREEN  = "\033[92m"
CYAN   = "\033[96m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

# ---------------------------------------------------------------------------
# Provider registry
# ---------------------------------------------------------------------------
@dataclass
class Provider:
    name: str
    hq: str           # Company HQ country
    data_region: str  # Where data is processed
    gdpr_risk: str    # "low" | "medium" | "high"
    notes: str


PROVIDER_MAP: dict[str, Provider] = {
    # OpenAI models
    "gpt-3.5-turbo": Provider("OpenAI", "USA", "USA", "high",
        "Data processed in US; SCCs required for EU transfers. Zero-data-retention opt-in available."),
    "gpt-4o": Provider("OpenAI", "USA", "USA", "high",
        "Same as GPT-3.5. Enterprise tier offers DPA + ZDR."),
    "gpt-4o-mini": Provider("OpenAI", "USA", "USA", "high",
        "Same as GPT-4o."),

    # Anthropic models
    "claude-sonnet-4-6": Provider("Anthropic", "USA", "USA", "high",
        "Data processed in US. Claude.ai commercial API has DPA available."),
    "claude-opus-4-6": Provider("Anthropic", "USA", "USA", "high",
        "Same as Claude Sonnet."),
    "claude-haiku-4-5": Provider("Anthropic", "USA", "USA", "high",
        "Same as Claude Sonnet."),

    # Google models
    "gemini-pro": Provider("Google", "USA", "EU/USA", "medium",
        "Google Cloud offers EU data residency. Vertex AI has GDPR DPA."),
    "gemini-flash": Provider("Google", "USA", "EU/USA", "medium",
        "Same as Gemini Pro."),

    # EU-hosted alternatives
    "scaleway-llm": Provider("Scaleway", "France", "EU (Paris)", "low",
        "GDPR-native EU provider. Data stays in France. Recommended for sensitive data."),
    "mistral-large": Provider("Mistral", "France", "EU (Paris)", "low",
        "EU-based, GDPR compliant by default. La Plateforme."),
    "mistral-7b": Provider("Mistral", "France", "EU (Paris)", "low",
        "Open-source, can run locally or EU-hosted."),

    # Local models (no data leaves device)
    "ollama-llama3": Provider("Local (Ollama)", "N/A", "Local device", "low",
        "No data leaves the device. Ideal for sensitive workloads."),
    "lm-studio": Provider("Local (LM Studio)", "N/A", "Local device", "low",
        "No data leaves the device."),
}

# Codebase-indexing agents (high IP risk)
CODEBASE_INDEXING_TOOLS = {
    "CodeAssist", "GitCopilot", "CursorAI", "Tabnine", "CodeWhisperer",
}

# Tools that typically handle sensitive business data
SENSITIVE_TOOLS = {
    "DocAnalyzer", "DataSummarizer", "TicketHelper",
}


def get_provider(model_name: str) -> Provider:
    if model_name in PROVIDER_MAP:
        return PROVIDER_MAP[model_name]
    # Fuzzy match
    model_lower = model_name.lower()
    if "gpt" in model_lower or "openai" in model_lower:
        return PROVIDER_MAP["gpt-4o"]
    if "claude" in model_lower:
        return PROVIDER_MAP["claude-sonnet-4-6"]
    if "gemini" in model_lower:
        return PROVIDER_MAP["gemini-pro"]
    if "mistral" in model_lower:
        return PROVIDER_MAP["mistral-large"]
    if "ollama" in model_lower or "llama" in model_lower or "local" in model_lower:
        return PROVIDER_MAP["ollama-llama3"]
    return Provider("Unknown", "Unknown", "Unknown", "high",
                    "Unknown provider — treat as high risk.")


def analyze_flow(records: list[dict]) -> dict:
    provider_stats: dict[str, dict] = defaultdict(lambda: {
        "count": 0, "total_tokens": 0, "total_cost": 0.0,
        "tools": set(), "departments": set(), "risks": [],
    })

    codebase_risks = []
    non_eu_sensitive = []

    for i, r in enumerate(records, 1):
        model    = r.get("model_name", "unknown")
        tool     = r.get("tool_name", "unknown")
        dept     = r.get("department_id", "unknown")
        tokens   = int(r.get("token_count", 0))
        cost     = float(r.get("cost", 0))
        region   = r.get("region", "unknown")
        rec_id   = r.get("id", f"line-{i}")

        provider = get_provider(model)
        key = provider.name

        provider_stats[key]["count"] += 1
        provider_stats[key]["total_tokens"] += tokens
        provider_stats[key]["total_cost"] += cost
        provider_stats[key]["tools"].add(tool)
        provider_stats[key]["departments"].add(dept)

        # Flag: codebase indexing agents sending to US providers
        if tool in CODEBASE_INDEXING_TOOLS and provider.gdpr_risk == "high":
            codebase_risks.append({
                "id": rec_id, "tool": tool, "model": model,
                "provider": provider.name, "dept": dept,
                "risk": "Agent may index codebase and send IP to non-EU provider",
            })

        # Flag: sensitive tool sending to non-EU provider
        if tool in SENSITIVE_TOOLS and provider.data_region not in ("EU (Paris)", "Local device"):
            non_eu_sensitive.append({
                "id": rec_id, "tool": tool, "model": model,
                "provider": provider.name, "data_region": provider.data_region,
                "dept": dept,
            })

    return {
        "provider_stats": {k: {**v, "tools": list(v["tools"]),
                                "departments": list(v["departments"])}
                           for k, v in provider_stats.items()},
        "codebase_index_risks": codebase_risks,
        "non_eu_sensitive_transfers": non_eu_sensitive,
    }


def print_report(analysis: dict) -> None:
    print(f"\n{BOLD}=== Provider Data Flow Report ==={RESET}\n")

    print(f"{BOLD}Provider Breakdown:{RESET}")
    for provider_name, stats in sorted(analysis["provider_stats"].items(),
                                        key=lambda x: -x[1]["total_cost"]):
        info = next((p for p in PROVIDER_MAP.values() if p.name == provider_name), None)
        risk_color = RED if info and info.gdpr_risk == "high" else (
                     YELLOW if info and info.gdpr_risk == "medium" else GREEN)
        region = info.data_region if info else "Unknown"
        risk   = info.gdpr_risk  if info else "unknown"
        print(f"\n  {BOLD}{provider_name}{RESET}")
        print(f"    Region : {region} | GDPR Risk: {risk_color}{risk}{RESET}")
        print(f"    Events : {stats['count']:,} | Tokens: {stats['total_tokens']:,} | Cost: €{stats['total_cost']:.2f}")
        print(f"    Tools  : {', '.join(stats['tools'])}")
        print(f"    Depts  : {', '.join(stats['departments'])}")
        if info:
            print(f"    Notes  : {info.notes}")

    risks = analysis["codebase_index_risks"]
    if risks:
        print(f"\n{RED}{BOLD}[!!] Codebase Indexing Risks ({len(risks)} events):{RESET}")
        for r in risks:
            print(f"  - {r['id']} | {r['tool']} → {r['provider']} | {r['dept']}")
            print(f"    {r['risk']}")
    else:
        print(f"\n{GREEN}No codebase indexing risks detected.{RESET}")

    transfers = analysis["non_eu_sensitive_transfers"]
    if transfers:
        print(f"\n{YELLOW}{BOLD}[!] Sensitive Data → Non-EU Providers ({len(transfers)} events):{RESET}")
        for t in transfers:
            print(f"  - {t['id']} | {t['tool']} → {t['provider']} ({t['data_region']}) | {t['dept']}")
    else:
        print(f"\n{GREEN}No non-EU sensitive transfers detected.{RESET}")

    print(f"\n{CYAN}Recommendation: Replace high-risk providers with:{RESET}")
    print(f"  - Scaleway AI (EU, GDPR-native): https://www.scaleway.com/en/")
    print(f"  - Mistral (France): https://mistral.ai/")
    print(f"  - Local Ollama/LM Studio for highest-sensitivity workloads")


def main(file_path: Path) -> int:
    records = []
    with file_path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

    analysis = analyze_flow(records)
    print_report(analysis)

    out_path = Path("provider_flow_report.json")
    with out_path.open("w") as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    print(f"\nFull report saved: {out_path}")

    has_risks = bool(
        analysis["codebase_index_risks"] or
        analysis["non_eu_sensitive_transfers"]
    )
    return 1 if has_risks else 0


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Analyze data flows to AI providers")
    parser.add_argument("--file", default="logs.jsonl")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        raise SystemExit(f"File not found: {path}")

    sys.exit(main(path))
