"""Background scheduler — cron jobs and periodic tasks.

Uses APScheduler for scheduled background work. Does NOT auto-start —
must be explicitly enabled via `task scheduler` or env var.

Usage:
    from app.scheduler import create_scheduler
    scheduler = create_scheduler()
    scheduler.start()
"""

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

log = structlog.get_logger()


async def sync_data_sources():
    """Example cron job: sync registered data sources."""
    log.info("cron_sync_data_sources", status="started")
    # TODO: Iterate DataSource entities, fetch new data, ingest
    log.info("cron_sync_data_sources", status="completed")


async def cleanup_expired_sessions():
    """Example cron job: clean up expired Redis sessions."""
    log.info("cron_cleanup_sessions", status="started")
    # TODO: Scan Redis for expired session keys
    log.info("cron_cleanup_sessions", status="completed")


async def refresh_analytics():
    """Example cron job: refresh DuckDB materialized tables."""
    log.info("cron_refresh_analytics", status="started")
    # TODO: Re-run DuckDB queries to refresh insights tables
    log.info("cron_refresh_analytics", status="completed")


def create_scheduler() -> AsyncIOScheduler:
    """Create the scheduler with all registered jobs."""
    scheduler = AsyncIOScheduler()

    # Data source sync — every 30 minutes
    scheduler.add_job(
        sync_data_sources,
        trigger=IntervalTrigger(minutes=30),
        id="sync_data_sources",
        name="Sync external data sources",
        replace_existing=True,
    )

    # Session cleanup — daily at 3am
    scheduler.add_job(
        cleanup_expired_sessions,
        trigger=CronTrigger(hour=3, minute=0),
        id="cleanup_sessions",
        name="Clean up expired sessions",
        replace_existing=True,
    )

    # Analytics refresh — every hour
    scheduler.add_job(
        refresh_analytics,
        trigger=IntervalTrigger(hours=1),
        id="refresh_analytics",
        name="Refresh DuckDB analytics",
        replace_existing=True,
    )

    return scheduler
