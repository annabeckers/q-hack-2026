"""
Dashboard Aggregator (Step 9 / Core Analytics)

Produces the core dashboard views from logs.jsonl:
  - Cost & usage per department
  - Cost & usage per model
  - Cost & usage per tool
  - Low-value / trivial-question detection
  - Private usage pattern detection
  - Future legislation readiness score

Usage:
    python dashboard_aggregator.py [--file logs.jsonl] [--json]
"""

import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# ANSI
# ---------------------------------------------------------------------------
BOLD   = "\033[1m"
CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
RESET  = "\033[0m"

# ---------------------------------------------------------------------------
# Low-value / trivial use detection
# ---------------------------------------------------------------------------
TRIVIAL_PATTERNS = [
    "wie viel uhr", "wetter", "what time", "weather",
    "rezept", "recipe", "joke", "witz", "urlaub", "holiday",
    "sport", "fußball", "football", "kino", "cinema", "film",
    "netflix", "youtube", "instagram", "facebook",
    "was ist", "what is", "who is", "wer ist",
]

PRIVATE_PATTERNS = [
    "mein lebenslauf", "my cv", "bewerbung", "cover letter",
    "dating", "tinder", "beziehung", "relationship",
    "urlaub", "vacation", "reise", "travel",
    "privatkredit", "loan", "kredit", "mortgage",
    "hobby", "rezept", "recipe", "kochen", "cooking",
]

# Max tokens to still count as "trivial" (short exchange)
TRIVIAL_TOKEN_THRESHOLD = 500


def is_trivial(record: dict) -> bool:
    tokens  = int(record.get("token_count", 9999))
    purpose = str(record.get("purpose", "")).lower()
    if tokens > TRIVIAL_TOKEN_THRESHOLD:
        return False
    return any(kw in purpose for kw in TRIVIAL_PATTERNS)


def is_private(record: dict) -> bool:
    purpose = str(record.get("purpose", "")).lower()
    return any(kw in purpose for kw in PRIVATE_PATTERNS)


# ---------------------------------------------------------------------------
# Aggregation helpers
# ---------------------------------------------------------------------------
def load_records(path: Path) -> list[dict]:
    records = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return records


def agg_by(records: list[dict], key: str) -> dict:
    buckets: dict[str, dict] = defaultdict(lambda: {
        "events": 0, "tokens": 0, "cost": 0.0,
        "trivial": 0, "private": 0,
    })
    for r in records:
        k = str(r.get(key, "unknown"))
        buckets[k]["events"]  += 1
        buckets[k]["tokens"]  += int(r.get("token_count", 0))
        buckets[k]["cost"]    += float(r.get("cost", 0))
        if is_trivial(r):
            buckets[k]["trivial"] += 1
        if is_private(r):
            buckets[k]["private"] += 1
    return dict(buckets)


def bar(value: float, max_val: float, width: int = 30) -> str:
    filled = int((value / max_val) * width) if max_val > 0 else 0
    return "█" * filled + "░" * (width - filled)


def print_table(title: str, data: dict, sort_by: str = "cost", color: str = CYAN) -> None:
    sorted_items = sorted(data.items(), key=lambda x: -x[1][sort_by])
    max_cost = max((v["cost"] for v in data.values()), default=1)

    print(f"\n{color}{BOLD}{title}{RESET}")
    print(f"  {'Key':<28} {'Events':>7} {'Tokens':>10} {'Cost €':>8}  {'Trivial':>7}  {'Private':>7}  Usage")
    print(f"  {'─'*28} {'─'*7} {'─'*10} {'─'*8}  {'─'*7}  {'─'*7}  {'─'*30}")
    for k, v in sorted_items:
        b = bar(v["cost"], max_cost)
        print(f"  {k:<28} {v['events']:>7,} {v['tokens']:>10,} {v['cost']:>8.2f}  "
              f"{v['trivial']:>7}  {v['private']:>7}  {b}")


def legislation_score(records: list[dict]) -> dict:
    """
    Quick EU AI Act readiness score:
    - Has purpose field: +20
    - Has region field: +20
    - Has model_name: +20
    - Has department_id: +20
    - Has user_id_hash (not real name): +20
    """
    if not records:
        return {"score": 0, "details": []}

    checks = {
        "purpose logged":        sum(1 for r in records if r.get("purpose")),
        "region logged":         sum(1 for r in records if r.get("region")),
        "model_name logged":     sum(1 for r in records if r.get("model_name")),
        "department_id logged":  sum(1 for r in records if r.get("department_id")),
        "user pseudonymized":    sum(1 for r in records if r.get("user_id_hash")),
    }
    n = len(records)
    score = sum(int(v / n * 100) for v in checks.values()) // len(checks)
    details = [{"check": k, "pct": int(v / n * 100)} for k, v in checks.items()]
    return {"score": score, "details": details}


def print_legislation(score_data: dict) -> None:
    score = score_data["score"]
    color = GREEN if score >= 80 else (YELLOW if score >= 50 else RED)
    print(f"\n{BOLD}EU AI Act / Future Legislation Readiness:{RESET}")
    print(f"  Overall score: {color}{BOLD}{score}/100{RESET}")
    for d in score_data["details"]:
        pct = d["pct"]
        c = GREEN if pct >= 80 else (YELLOW if pct >= 50 else RED)
        print(f"  {d['check']:<30} {c}{pct:>3}%{RESET}")


def main(file_path: Path, as_json: bool = False) -> None:
    records = load_records(file_path)
    if not records:
        print("No records found.")
        return

    by_dept  = agg_by(records, "department_id")
    by_model = agg_by(records, "model_name")
    by_tool  = agg_by(records, "tool_name")
    leg      = legislation_score(records)

    if as_json:
        output = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_records": len(records),
            "by_department": by_dept,
            "by_model": by_model,
            "by_tool": by_tool,
            "legislation_readiness": leg,
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return

    total_cost   = sum(float(r.get("cost", 0)) for r in records)
    total_tokens = sum(int(r.get("token_count", 0)) for r in records)
    trivial_ct   = sum(1 for r in records if is_trivial(r))
    private_ct   = sum(1 for r in records if is_private(r))

    print(f"\n{BOLD}=== AI Usage Dashboard ==={RESET}")
    print(f"  File    : {file_path}")
    print(f"  Records : {len(records):,}")
    print(f"  Tokens  : {total_tokens:,}")
    print(f"  Total €  : {total_cost:.2f}")
    print(f"  Trivial : {trivial_ct} ({trivial_ct/len(records)*100:.1f}%) — potential waste")
    print(f"  Private : {private_ct} ({private_ct/len(records)*100:.1f}%) — policy risk")

    print_table("By Department",  by_dept,  color=CYAN)
    print_table("By Model",       by_model, color=GREEN)
    print_table("By Tool",        by_tool,  color=YELLOW)
    print_legislation(leg)

    print(f"\n{CYAN}Low-cost alternatives for trivial use cases:{RESET}")
    print("  - Scaleway AI  → https://www.scaleway.com/en/ (EU, GDPR-native)")
    print("  - Mistral 7B   → local or EU-hosted, cheap for simple Q&A")
    print("  - Ollama local → free, zero data leakage")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Dashboard analytics from logs.jsonl")
    parser.add_argument("--file", default="logs.jsonl")
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of table")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        raise SystemExit(f"File not found: {path}")

    main(path, as_json=args.json)
