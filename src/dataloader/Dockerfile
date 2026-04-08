# syntax=docker/dockerfile:1

FROM python:3.12-slim AS base
WORKDIR /app

# System deps for kreuzberg PDF extraction (cached layer)
RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 poppler-utils tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Dependencies (cached — only rebuilds when pyproject.toml changes)
COPY pyproject.toml uv.lock* ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# Source (changes frequently — last layer)
COPY . .

CMD ["uv", "run", "python", "-m", "dataloader.main"]
