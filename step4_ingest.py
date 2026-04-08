"""
Step 4: Ingest logs.jsonl into PostgreSQL and verify the result.

Usage:
    python step4_ingest.py [--file logs.jsonl]

Install dependency:
    pip install psycopg2-binary

Connection defaults match docker-compose.yml:
    host=localhost  port=5432  db=ai_usage  user=postgres  password=hackathon
Override via environment variables:
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
"""

import json
import os
import sys
from pathlib import Path

try:
    import psycopg2
    from psycopg2.extras import execute_values
except ImportError:
    raise SystemExit("Missing dependency: pip install psycopg2-binary")

# --- Connection config (override with env vars) ---
DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     int(os.getenv("DB_PORT", 5432)),
    "dbname":   os.getenv("DB_NAME", "ai_usage"),
    "user":     os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "hackathon"),
}

UPSERT_SQL = """
INSERT INTO tools_usage
    (id, user_id_hash, department_id, tool_name, model_name,
     usage_start, usage_end, token_count, cost, purpose, region)
VALUES %s
ON CONFLICT (id) DO UPDATE SET
    token_count  = EXCLUDED.token_count,
    cost         = EXCLUDED.cost,
    ingested_at  = NOW();
"""


def load_jsonl(path: Path) -> list[dict]:
    records = []
    with path.open() as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"  Warning: skipping line {i} — {e}")
    return records


def to_row(r: dict) -> tuple:
    return (
        r["id"],
        r["user_id_hash"],
        r["department_id"],
        r["tool_name"],
        r["model_name"],
        r["usage_start"],
        r["usage_end"],
        int(r["token_count"]),
        float(r["cost"]),
        r.get("purpose"),
        r.get("region"),
    )


def ingest(records: list[dict], conn) -> int:
    rows = [to_row(r) for r in records]
    with conn.cursor() as cur:
        execute_values(cur, UPSERT_SQL, rows)
    conn.commit()
    return len(rows)


def verify(conn) -> int:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM tools_usage;")
        return cur.fetchone()[0]


def main(file_path: Path) -> None:
    print(f"Loading {file_path}...")
    records = load_jsonl(file_path)
    print(f"  {len(records)} records parsed.")

    print(f"Connecting to PostgreSQL at {DB_CONFIG['host']}:{DB_CONFIG['port']}...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        raise SystemExit(f"Connection failed: {e}")

    print("Ingesting (UPSERT)...")
    count = ingest(records, conn)
    print(f"  {count} rows upserted.")

    total = verify(conn)
    print(f"\nVerification: SELECT COUNT(*) FROM tools_usage → {total} rows total.")

    conn.close()
    print("Done.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Ingest logs.jsonl into PostgreSQL")
    parser.add_argument("--file", default="logs.jsonl", help="Path to JSONL file")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        raise SystemExit(f"File not found: {path}")

    main(path)
