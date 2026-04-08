"""Analysis worker — polls for unprocessed chats and runs all analyzers.

This is the single entry point that orchestrates deterministic + LLM analysis.
Each analyzer is idempotent: it skips messages it already has findings for.

Usage:
    python scripts/run_analysis_worker.py                # single run
    python scripts/run_analysis_worker.py --loop          # continuous polling
    python scripts/run_analysis_worker.py --loop --interval 15
    python scripts/run_analysis_worker.py --only llm      # only LLM analyzers
    python scripts/run_analysis_worker.py --only det      # only deterministic
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("analysis-worker")


async def run_deterministic(batch_size: int) -> dict[str, int]:
    """Run deterministic analyzers — secrets, PII, slopsquatting (regex-based)."""
    from app.application.services.deterministic_extraction import run_deterministic_extraction
    return await run_deterministic_extraction(batch_size=batch_size)


async def run_llm(batch_size: int) -> dict[str, int]:
    """Run LLM-based analyzers (Gemini Flash)."""
    from app.application.services.llm_extraction import run_llm_extraction
    return await run_llm_extraction(batch_size=batch_size)


async def refresh_dashboard() -> None:
    """Refresh materialized views so frontend reads fresh data."""
    from sqlalchemy import text
    from app.infrastructure.database import async_session_factory

    async with async_session_factory() as session:
        async with session.begin():
            await session.execute(text("SELECT refresh_dashboard_views()"))
    logger.info("Dashboard views refreshed")


async def run_all(batch_size: int, only: str | None = None) -> dict[str, int]:
    """Run all analyzers and refresh dashboard views."""
    stats: dict[str, int] = {}

    if only in (None, "det"):
        det_stats = await run_deterministic(batch_size)
        stats.update(det_stats)

    if only in (None, "llm"):
        llm_stats = await run_llm(batch_size)
        stats.update(llm_stats)

    # Refresh frontend-facing views after analysis
    if sum(stats.values()) > 0:
        await refresh_dashboard()

    return stats


async def main() -> None:
    parser = argparse.ArgumentParser(description="Analysis worker — process unanalyzed chat messages")
    parser.add_argument("--batch-size", type=int, default=20)
    parser.add_argument("--only", choices=["det", "llm"], help="Run only deterministic or LLM analyzers")
    parser.add_argument("--loop", action="store_true", help="Run continuously")
    parser.add_argument("--interval", type=int, default=15, help="Seconds between runs in loop mode")
    args = parser.parse_args()

    if args.loop:
        logger.info("Worker started in loop mode (interval: %ds)", args.interval)
        while True:
            stats = await run_all(args.batch_size, only=args.only)
            total = sum(stats.values())
            if total > 0:
                logger.info("Produced %d findings: %s", total, stats)
            else:
                logger.debug("No new findings — sleeping %ds", args.interval)
            await asyncio.sleep(args.interval)
    else:
        stats = await run_all(args.batch_size, only=args.only)
        total = sum(stats.values())
        print(f"Results: {stats}")
        print(f"Total findings: {total}")


if __name__ == "__main__":
    asyncio.run(main())
