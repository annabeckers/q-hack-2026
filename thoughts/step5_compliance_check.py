"""
Step 5: Security & compliance validator for logs.jsonl.

Checks each record for:
  - PII patterns (email, phone, real names, IP addresses)
  - Unredacted sensitive field values
  - Schema completeness
  - Cost/token anomalies

Usage:
    python step5_compliance_check.py [--file logs.jsonl]

Exit code: 0 = all clear, 1 = issues found.
"""

import json
import re
import sys
from pathlib import Path

# --- PII detection patterns ---
PII_PATTERNS = {
    "email":       re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"),
    "phone_de":    re.compile(r"(\+49|0)[1-9]\d{6,14}"),
    "ipv4":        re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    "iban":        re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7,}(?:[A-Z0-9]{0,3})\b"),
}

# Fields that must never contain free-text PII
TEXT_FIELDS = {"purpose", "prompt", "content", "message", "text", "query"}

# Required fields for schema completeness
REQUIRED_FIELDS = {
    "id", "user_id_hash", "department_id", "tool_name",
    "model_name", "usage_start", "usage_end", "token_count", "cost",
}

# Anomaly thresholds
MAX_TOKEN_COUNT = 100_000
MAX_COST = 100.0


def check_record(record: dict, line_num: int) -> list[str]:
    issues = []

    # 1. Schema completeness
    for field in REQUIRED_FIELDS:
        if field not in record:
            issues.append(f"Line {line_num}: missing required field '{field}'")

    # 2. user_id_hash must look hashed, not like a real name/email
    uid = str(record.get("user_id_hash", ""))
    if "@" in uid or " " in uid:
        issues.append(f"Line {line_num}: 'user_id_hash' looks like PII: '{uid[:30]}'")

    # 3. Scan text fields for PII patterns
    for field in TEXT_FIELDS:
        value = str(record.get(field, ""))
        if value in ("[REDACTED]", ""):
            continue
        for pii_name, pattern in PII_PATTERNS.items():
            if pattern.search(value):
                issues.append(
                    f"Line {line_num}: PII detected ({pii_name}) in field '{field}': '{value[:60]}'"
                )

    # 4. Scan ALL string values for PII (belt-and-suspenders)
    for key, value in record.items():
        if key in TEXT_FIELDS:
            continue  # already checked above
        value_str = str(value)
        for pii_name, pattern in PII_PATTERNS.items():
            if pattern.search(value_str):
                issues.append(
                    f"Line {line_num}: PII detected ({pii_name}) in field '{key}': '{value_str[:60]}'"
                )

    # 5. Anomaly checks
    try:
        tokens = int(record.get("token_count", 0))
        if tokens > MAX_TOKEN_COUNT:
            issues.append(f"Line {line_num}: token_count {tokens} exceeds limit {MAX_TOKEN_COUNT}")
        if tokens < 0:
            issues.append(f"Line {line_num}: token_count is negative ({tokens})")
    except (TypeError, ValueError):
        issues.append(f"Line {line_num}: token_count is not a valid integer")

    try:
        cost = float(record.get("cost", 0))
        if cost > MAX_COST:
            issues.append(f"Line {line_num}: cost {cost} exceeds limit {MAX_COST}")
        if cost < 0:
            issues.append(f"Line {line_num}: cost is negative ({cost})")
    except (TypeError, ValueError):
        issues.append(f"Line {line_num}: cost is not a valid number")

    return issues


def check_file(path: Path) -> list[str]:
    all_issues = []
    seen_ids = {}

    with path.open() as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as e:
                all_issues.append(f"Line {line_num}: invalid JSON — {e}")
                continue

            # Duplicate ID check
            record_id = record.get("id")
            if record_id in seen_ids:
                all_issues.append(
                    f"Line {line_num}: duplicate id '{record_id}' (first seen on line {seen_ids[record_id]})"
                )
            else:
                seen_ids[record_id] = line_num

            all_issues.extend(check_record(record, line_num))

    return all_issues


def main(file_path: Path) -> int:
    print(f"Compliance check: {file_path}")
    print("-" * 50)

    issues = check_file(file_path)

    if not issues:
        print("All checks passed. No PII or compliance issues found.")
        return 0
    else:
        print(f"Found {len(issues)} issue(s):\n")
        for issue in issues:
            print(f"  [FAIL] {issue}")
        return 1


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Compliance validator for logs.jsonl")
    parser.add_argument("--file", default="logs.jsonl", help="Path to JSONL file")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        raise SystemExit(f"File not found: {path}")

    sys.exit(main(path))
