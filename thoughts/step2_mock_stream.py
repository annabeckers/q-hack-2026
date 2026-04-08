"""
Step 2: Simulate a real-time event stream of AI usage logs using Faker.

Usage:
    # Append 10 events once:
    python step2_mock_stream.py --count 10

    # Stream continuously every 2 seconds (Ctrl+C to stop):
    python step2_mock_stream.py --stream --interval 2

Install dependency:
    pip install faker
"""

import argparse
import json
import random
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    from faker import Faker
except ImportError:
    raise SystemExit("Missing dependency: pip install faker")

fake = Faker("de_DE")

OUTPUT_FILE = Path("logs.jsonl")

TOOLS = ["ChatComposer", "CodeAssist", "SummaryBot", "CopyWriter", "DocAnalyzer",
         "DataSummarizer", "TicketHelper"]
MODELS = ["gpt-3.5-turbo", "gpt-4o", "gpt-4o-mini",
          "claude-sonnet-4-6", "claude-opus-4-6", "claude-haiku-4-5"]
DEPARTMENTS = ["dept-finance", "dept-engineering", "dept-hr", "dept-marketing",
               "dept-legal", "dept-support", "dept-product", "dept-data",
               "dept-sales", "dept-security"]
PURPOSES = [
    "Budgetanalyse", "Code-Review", "Dokumentation erstellen",
    "E-Mail verfassen", "Datenauswertung", "Ticket-Klassifikation",
    "Vertragsprüfung", "Marketingtext", "Onboarding-Material",
    "KPI-Bericht", "Feature-Spezifikation", "Security-Audit",
]
REGIONS = ["eu-west", "eu-central"]

# Cost per 1k tokens (approximate, per model)
COST_PER_1K = {
    "gpt-3.5-turbo": 0.0015,
    "gpt-4o": 0.005,
    "gpt-4o-mini": 0.00015,
    "claude-sonnet-4-6": 0.003,
    "claude-opus-4-6": 0.015,
    "claude-haiku-4-5": 0.00025,
}

# Stable user pool (pseudonymous)
USER_POOL = [f"u{i}-hash" for i in range(1, 21)]

_log_counter = 0


def next_log_id() -> str:
    global _log_counter
    _log_counter += 1
    return f"log-stream-{uuid.uuid4().hex[:8]}"


def generate_event() -> dict:
    model = random.choice(MODELS)
    tool = random.choice(TOOLS)
    token_count = random.randint(200, 10000)
    cost_per_k = COST_PER_1K.get(model, 0.002)
    cost = round(token_count / 1000 * cost_per_k, 4)

    duration_minutes = random.randint(1, 30)
    start = datetime.now(timezone.utc) - timedelta(minutes=random.randint(0, 60))
    end = start + timedelta(minutes=duration_minutes)

    return {
        "id": next_log_id(),
        "user_id_hash": random.choice(USER_POOL),
        "department_id": random.choice(DEPARTMENTS),
        "tool_name": tool,
        "model_name": model,
        "usage_start": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "usage_end": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "token_count": token_count,
        "cost": cost,
        "purpose": random.choice(PURPOSES),
        "region": random.choice(REGIONS),
    }


def append_events(count: int) -> None:
    with OUTPUT_FILE.open("a") as f:
        for _ in range(count):
            event = generate_event()
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
            print(f"  + {event['id']} | {event['tool_name']} | {event['model_name']} | {event['token_count']} tokens")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mock AI usage event stream")
    parser.add_argument("--count", type=int, default=5, help="Number of events to generate per batch")
    parser.add_argument("--stream", action="store_true", help="Run continuously until Ctrl+C")
    parser.add_argument("--interval", type=float, default=3.0, help="Seconds between batches (stream mode)")
    args = parser.parse_args()

    if args.stream:
        print(f"Streaming to {OUTPUT_FILE} every {args.interval}s (Ctrl+C to stop)...")
        try:
            while True:
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Appending {args.count} event(s):")
                append_events(args.count)
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\nStream stopped.")
    else:
        print(f"Appending {args.count} event(s) to {OUTPUT_FILE}:")
        append_events(args.count)
        print("Done.")
