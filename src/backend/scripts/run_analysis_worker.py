"""Analysis worker — polls for unprocessed chats and runs all analyzers.

Architecture: Runs as a separate Docker service (same image, different entrypoint).
Decoupled from the API — if the worker crashes, the API keeps serving cached views.

Each analyzer is idempotent: it skips messages it already has findings for.
After producing findings, refreshes materialized views for the dashboard.

Usage:
    python scripts/run_analysis_worker.py                # single run
    python scripts/run_analysis_worker.py --loop          # continuous (default interval: 30s)
    python scripts/run_analysis_worker.py --loop --interval 15
    python scripts/run_analysis_worker.py --only llm      # only LLM analyzers
    python scripts/run_analysis_worker.py --only det      # only deterministic
"""

from __future__ import annotations

import argparse
import asyncio
import signal
import sys
from pathlib import Path

import structlog

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

log = structlog.get_logger("analysis-worker")

# Graceful shutdown flag
_shutdown = asyncio.Event()


def _handle_signal(sig: signal.Signals) -> None:
    log.info("shutdown_signal", signal=sig.name)
    _shutdown.set()


async def run_deterministic(batch_size: int) -> dict[str, int]:
    """Run deterministic analyzers — secrets, PII, slopsquatting (regex-based)."""
    try:
        from app.application.services.deterministic_extraction import run_deterministic_extraction
        return await run_deterministic_extraction(batch_size=batch_size)
    except Exception as e:
        log.error("deterministic_failed", error=str(e))
        return {}


async def run_llm(batch_size: int) -> dict[str, int]:
    """Run LLM-based analyzers (Gemini Flash)."""
    try:
        from app.application.services.llm_extraction import run_llm_extraction
        return await run_llm_extraction(batch_size=batch_size)
    except Exception as e:
        log.error("llm_failed", error=str(e))
        return {}


async def run_meta_analysis() -> int:
    """Run meta-analyzer on chats that have findings but no insight record yet."""
    try:
        from app.application.services.meta_analysis import run_meta_analysis_for_pending_chats
        return await run_meta_analysis_for_pending_chats()
    except Exception as e:
        log.error("meta_analysis_failed", error=str(e))
        return 0


async def refresh_dashboard() -> None:
    """Refresh materialized views so frontend reads fresh data."""
    from sqlalchemy import text
    from app.infrastructure.database import async_session_factory

    async with async_session_factory() as session:
        async with session.begin():
            await session.execute(text("SELECT refresh_dashboard_views()"))
    log.info("dashboard_views_refreshed")


HEALTH_FILE = Path("/tmp/worker-healthy")


async def run_cycle(batch_size: int, only: str | None = None) -> dict[str, int]:
    """Run one analysis cycle: analyzers → refresh dashboard."""
    stats: dict[str, int] = {}

    if only in (None, "det"):
        det_stats = await run_deterministic(batch_size)
        stats.update(det_stats)

    if only in (None, "llm"):
        llm_stats = await run_llm(batch_size)
        stats.update(llm_stats)

    # Run meta-analysis *after* raw findings are generated
    insights_created = await run_meta_analysis()
    if insights_created > 0:
        stats["meta_insights"] = insights_created

    # Refresh frontend-facing views after producing new findings
    if sum(stats.values()) > 0:
        await refresh_dashboard()
        
    # Generate system recommendations
    try:
        from app.application.services.recommendation_engine import generate_system_recommendations
        rec_count = await generate_system_recommendations()
        if rec_count > 0:
            stats["new_recommendations"] = rec_count
    except Exception as e:
        log.error("recommendation_engine_failed", error=str(e))

    # Touch health file for Docker health check
    HEALTH_FILE.write_text("ok")

    return stats


async def main() -> None:
    parser = argparse.ArgumentParser(description="Analysis worker — process unanalyzed chat messages")
    parser.add_argument("--batch-size", type=int, default=20)
    parser.add_argument("--only", choices=["det", "llm"], help="Run only deterministic or LLM analyzers")
    parser.add_argument("--loop", action="store_true", help="Run continuously")
    parser.add_argument("--interval", type=int, default=30, help="Seconds between runs in loop mode")
    args = parser.parse_args()

    # Register signal handlers for graceful shutdown
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda s=sig: _handle_signal(s))

    if args.loop:
        log.info("worker_started", mode="loop", interval=args.interval, batch_size=args.batch_size)
        while not _shutdown.is_set():
            stats = await run_cycle(args.batch_size, only=args.only)
            total = sum(stats.values())
            if total > 0:
                log.info("cycle_complete", findings=total, breakdown=stats)
            else:
                log.debug("cycle_idle", message="no new findings")

            # Wait for interval or shutdown signal
            try:
                await asyncio.wait_for(_shutdown.wait(), timeout=args.interval)
            except asyncio.TimeoutError:
                pass  # Normal — interval elapsed, run next cycle

        log.info("worker_stopped", reason="shutdown signal")
    else:
        stats = await run_cycle(args.batch_size, only=args.only)
        total = sum(stats.values())
        log.info("single_run_complete", findings=total, breakdown=stats)


if __name__ == "__main__":
    asyncio.run(main())
