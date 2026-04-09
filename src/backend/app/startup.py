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

    # At least one AI provider should be configured
    ai_configured = any([
        settings.openai_api_key,
        settings.anthropic_api_key,
        settings.google_api_key,
        settings.aws_bedrock_model_id != "us.anthropic.claude-sonnet-4-6",
    ])
    if not ai_configured:
        warnings.append("No AI provider API key configured — agents will fail")

    # CORS should not be wildcard in production
    if settings.cors_origins == "*" and not settings.debug:
        warnings.append("CORS_ORIGINS is wildcard (*) — restrict for production")

    for w in warnings:
        log.warning("config_warning", message=w)

    return warnings


def log_startup_info() -> None:
    """Log configuration summary at startup."""
    db_type = "postgresql"
    log.info(
        "startup",
        database=db_type,
        redis=bool(settings.redis_url),
        neo4j=bool(settings.neo4j_uri),
        scheduler=settings.scheduler_enabled,
        debug=settings.debug,
    )
