"""
Step 1: Anonymize/pseudonymize real chat export data before use.

Usage:
    python step1_anonymize.py input_raw.jsonl output_anonymized.jsonl

What it does:
- Replaces real usernames/emails with stable hashes (same user → same hash)
- Strips any free-text fields that might contain PII
- Keeps only metadata fields safe for demo use
"""

import hashlib
import json
import sys
from pathlib import Path

# Fields to keep as-is (metadata only, no PII)
SAFE_FIELDS = {
    "id", "department_id", "tool_name", "model_name",
    "usage_start", "usage_end", "token_count", "cost", "region",
}

# Fields to hash (stable pseudonym: same input → same hash)
HASH_FIELDS = {"user_id", "username", "email", "user_email"}

# Fields to replace with a generic placeholder (free-text, may contain PII)
REDACT_FIELDS = {"purpose", "prompt", "content", "message", "text", "query"}


def stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:12] + "-hash"


def anonymize_record(record: dict) -> dict:
    result = {}
    for key, value in record.items():
        if key in SAFE_FIELDS:
            result[key] = value
        elif key in HASH_FIELDS:
            result["user_id_hash"] = stable_hash(str(value))
        elif key == "user_id_hash":
            # Already hashed — keep as-is
            result[key] = value
        elif key in REDACT_FIELDS:
            result[key] = "[REDACTED]"
        else:
            # Unknown field: redact by default (safe-by-default policy)
            result[key] = "[REDACTED]"
    return result


def anonymize_file(input_path: Path, output_path: Path) -> int:
    count = 0
    with input_path.open() as fin, output_path.open("w") as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            anonymized = anonymize_record(record)
            fout.write(json.dumps(anonymized, ensure_ascii=False) + "\n")
            count += 1
    return count


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python step1_anonymize.py <input.jsonl> <output.jsonl>")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    if not input_path.exists():
        print(f"Error: {input_path} not found.")
        sys.exit(1)

    count = anonymize_file(input_path, output_path)
    print(f"Anonymized {count} records → {output_path}")
    print("PII policy applied:")
    print(f"  Hashed fields : {HASH_FIELDS}")
    print(f"  Redacted fields: {REDACT_FIELDS}")
    print(f"  Safe fields   : {SAFE_FIELDS}")
