"""Startup validation — fail fast if config is broken."""

import structlog
from app.config import settings

log = structlog.get_logger()


def validate_environment() -> list[str]:
    """Check required configuration. Returns list of warnings (empty = all good)."""
    warnings = []

    # Database URL must be set
    if "change-me" in settings.database_url or not settings.database_url:
        warnings.append("DATABASE_URL is not configured")

    # LLM provider check
    if settings.model_provider == "gemini" and not settings.google_api_key:
        warnings.append("MODEL_PROVIDER=gemini but GOOGLE_API_KEY is not set — agents will fail")
    elif settings.model_provider == "openai" and not settings.openai_api_key:
        warnings.append("MODEL_PROVIDER=openai but OPENAI_API_KEY is not set — agents will fail")

    # CORS should not be wildcard in production
    if settings.cors_origins == "*" and not settings.debug:
        warnings.append("CORS_ORIGINS is wildcard (*) — restrict for production")

    for w in warnings:
        log.warning("config_warning", message=w)

    return warnings


def log_startup_info() -> None:
    """Log configuration summary at startup."""
    log.info(
        "startup",
        database="postgresql",
        redis=bool(settings.redis_url),
        neo4j=bool(settings.neo4j_uri),
        model_provider=settings.model_provider,
        debug=settings.debug,
    )
