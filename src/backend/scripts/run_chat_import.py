"""CLI entrypoint for chat export import."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.application.services.chat_import import import_chat_exports


async def main() -> None:
    parser = argparse.ArgumentParser(description="Import chat export files into PostgreSQL chats table")
    parser.add_argument(
        "--dir",
        dest="input_dir",
        default="../../../chat-exports",
        help="Path to chat export directory (relative to src/backend)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and profile rows without writing to database",
    )
    parser.add_argument("--claude-history", help="Path to Claude Code prompt history JSONL", default=None)
    parser.add_argument("--claude-projects-dir", help="Path to Claude Code projects directory", default=None)
    parser.add_argument("--pi-sessions-dir", help="Path to Pi Agent sessions directory", default=None)
    args = parser.parse_args()

    base = Path(__file__).resolve().parent
    input_dir = (base / args.input_dir).resolve()

    stats = await import_chat_exports(
        input_dir=input_dir,
        dry_run=args.dry_run,
        claude_history=Path(args.claude_history).expanduser() if args.claude_history else None,
        claude_projects_dir=Path(args.claude_projects_dir).expanduser() if args.claude_projects_dir else None,
        pi_sessions_dir=Path(args.pi_sessions_dir).expanduser() if args.pi_sessions_dir else None,
    )

    print(f"Processed local files: {stats.processed_local_files}")
    print(f"Extracted messages: {stats.extracted_messages}")
    print(f"Providers: {stats.providers}")
    print(f"Top files by message count: {stats.top_files}")
    if not args.dry_run:
        print(f"Inserted/updated rows in chats: {stats.inserted_or_updated}")


if __name__ == "__main__":
    asyncio.run(main())
