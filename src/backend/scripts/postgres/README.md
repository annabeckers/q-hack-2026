# PostgreSQL Setup

These scripts initialize PostgreSQL for local development.

## Automatic setup via Docker

The Postgres service in `docker-compose.yml` mounts this folder to `/docker-entrypoint-initdb.d`.
Scripts run on first database initialization:

1. `001_init_schema.sql`
2. `002_chats_schema.sql`

If the `postgres-data` volume already exists, these scripts will not run automatically again.

## Re-run manually

From project root:

```bash
docker compose exec -T postgres psql -U postgres -d hackathon -f /docker-entrypoint-initdb.d/001_init_schema.sql
docker compose exec -T postgres psql -U postgres -d hackathon -f /docker-entrypoint-initdb.d/002_chats_schema.sql
```

## Mock data seeding (Python)

Use the Python loader as the single source of truth for mock data:

- No authentication seed data is inserted.
- Seeds business datasets: `costumers`, `employees`, `documents`.

```bash
cd src/backend
uv run python scripts/seed_database.py
```

## Chat export import

Load JSON files from `chat-exports/` into PostgreSQL table `chats`:

```bash
cd src/backend
uv run python scripts/run_chat_import.py
```

User and model messages are imported, with privacy-aware metadata.

Optional: include local Claude Code / Pi Agent JSONL history during the same run:

```bash
uv run python scripts/run_chat_import.py \
	--claude-history ~/.claude/history.jsonl \
	--claude-projects-dir ~/.claude/projects \
	--pi-sessions-dir ~/.pi/agent/sessions
```
