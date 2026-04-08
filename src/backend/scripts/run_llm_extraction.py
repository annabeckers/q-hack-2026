"""CLI entrypoint for LLM-based chat analysis.

Usage:
    python scripts/run_llm_extraction.py                          # all analyzers, batch 20
    python scripts/run_llm_extraction.py --batch-size 50          # larger batch
    python scripts/run_llm_extraction.py --only llm_sensitivity   # single analyzer
    python scripts/run_llm_extraction.py --loop --interval 30     # continuous mode
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.application.services.llm_extraction import run_llm_extraction


async def main() -> None:
    parser = argparse.ArgumentParser(description="Run LLM extraction on chat messages")
    parser.add_argument("--batch-size", type=int, default=20, help="Messages per analyzer per run")
    parser.add_argument("--only", nargs="+", help="Run only these analyzers (llm_trivial, llm_sensitivity, llm_complexity)")
    parser.add_argument("--loop", action="store_true", help="Run continuously")
    parser.add_argument("--interval", type=int, default=30, help="Seconds between runs in loop mode")
    args = parser.parse_args()

    analyzers = args.only if args.only else None

    if args.loop:
        print(f"Running in loop mode (interval: {args.interval}s)")
        while True:
            stats = await run_llm_extraction(batch_size=args.batch_size, analyzers=analyzers)
            total = sum(stats.values())
            print(f"  Run complete: {stats} ({total} total findings)")
            if total == 0:
                print(f"  No unanalyzed messages — sleeping {args.interval}s")
            await asyncio.sleep(args.interval)
    else:
        stats = await run_llm_extraction(batch_size=args.batch_size, analyzers=analyzers)
        print(f"Results: {stats}")
        print(f"Total findings: {sum(stats.values())}")


if __name__ == "__main__":
    asyncio.run(main())
