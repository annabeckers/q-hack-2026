import sys
from importlib.metadata import version as pkg_version

from fastapi import APIRouter, Request
from sqlalchemy import text

router = APIRouter()


@router.get("/health")
async def health(request: Request):
    """Health check — verifies connectivity to Postgres."""
    checks = {
        "status": "ok",
        "python": sys.version.split()[0],
        "fastapi": pkg_version("fastapi"),
        "sqlalchemy": pkg_version("sqlalchemy"),
    }
    container = request.app.state.container

    # Postgres
    try:
        async with container.db_session_factory() as session:
            result = await session.execute(text("SELECT version()"))
            row = result.scalar()
            checks["postgres"] = row.split(",")[0] if row else "ok"
    except Exception as e:
        checks["postgres"] = f"error: {e}"
        checks["status"] = "degraded"

    # Redis
    try:
        if container.redis:
            info = await container.redis.info("server")
            checks["redis"] = f"ok (v{info.get('redis_version', '?')})"
    except Exception as e:
        checks["redis"] = f"error: {e}"
        checks["status"] = "degraded"

    # Neo4j
    try:
        if container.neo4j_driver:
            await container.neo4j_driver.verify_connectivity()
            checks["neo4j"] = "ok"
    except Exception as e:
        checks["neo4j"] = f"error: {e}"
        checks["status"] = "degraded"

    return checks
