"""Run the deterministic company-data vs chat-data analysis and persist results."""

from __future__ import annotations

import asyncio

from app.application.services.deterministic_analysis import default_deterministic_analysis_service


async def main() -> None:
    stats = await default_deterministic_analysis_service.run()
    print(f"Analysis run id: {stats['analysis_run_id']}")
    print(f"Source messages: {stats['source_message_count']}")
    print(f"Company rules: {stats['rule_count']}")
    print(f"Matches saved: {stats['match_count']}")
    print(f"Conversation summaries: {stats['conversation_count']}")


if __name__ == "__main__":
    asyncio.run(main())
