# syntax=docker/dockerfile:1

# ── Base ─────────────────────────────────────────
FROM python:3.12-slim AS base
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# ── Dependencies (cached layer — only rebuilds when pyproject.toml changes) ──
FROM base AS deps
COPY pyproject.toml uv.lock* ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --no-install-project

# ── Development ──────────────────────────────────
FROM deps AS dev
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-install-project
COPY . .
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ── Production ───────────────────────────────────
FROM deps AS prod
COPY . .
# Non-root user for security
RUN useradd -r -s /bin/false appuser
USER appuser
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
