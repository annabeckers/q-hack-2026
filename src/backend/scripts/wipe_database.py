"""Wipe all analysis data — findings, chats, and dashboard views.

Usage:
    python scripts/wipe_database.py              # interactive confirmation
    python scripts/wipe_database.py --confirm     # skip confirmation (CI/demo)
    python scripts/wipe_database.py --only findings  # wipe findings only, keep chats
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text


async def wipe(only: str | None = None) -> dict[str, int]:
    from app.infrastructure.database import async_session_factory

    stats: dict[str, int] = {}

    async with async_session_factory() as session:
        async with session.begin():
            # Always wipe findings first (FK constraint)
            result = await session.execute(text("DELETE FROM findings"))
            stats["findings"] = result.rowcount

            if only != "findings":
                result = await session.execute(text("DELETE FROM chats"))
                stats["chats"] = result.rowcount

            # Refresh materialized views to reflect empty state
            try:
                await session.execute(text("SELECT refresh_dashboard_views()"))
            except Exception:
                pass  # Views may not exist yet

    return stats


async def main() -> None:
    parser = argparse.ArgumentParser(description="Wipe analysis data")
    parser.add_argument("--confirm", action="store_true", help="Skip confirmation prompt")
    parser.add_argument("--only", choices=["findings"], help="Only wipe findings, keep chat data")
    args = parser.parse_args()

    if not args.confirm:
        target = "findings only" if args.only == "findings" else "ALL data (chats + findings)"
        answer = input(f"This will delete {target}. Type 'yes' to confirm: ")
        if answer.strip().lower() != "yes":
            print("Aborted.")
            return

    stats = await wipe(only=args.only)
    for table, count in stats.items():
        print(f"  {table}: {count} rows deleted")
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
