from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.container import Container
from app.middleware import setup_middleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Validate config on startup
    from app.startup import validate_environment, log_startup_info

    log_startup_info()
    validate_environment()

    # OpenTelemetry (if enabled — traces to Jaeger, metrics to Prometheus)
    from app.telemetry import setup_telemetry
    setup_telemetry(app)

    container = Container()
    await container.init()
    app.state.container = container

    # Start scheduler if enabled
    if settings.scheduler_enabled:
        from app.scheduler import create_scheduler

        scheduler = create_scheduler()
        scheduler.start()
        app.state.scheduler = scheduler

    yield

    if hasattr(app.state, "scheduler"):
        app.state.scheduler.shutdown()
    await container.close()


app = FastAPI(
    title="Hackathon API",
    description="Full-stack hackathon template with DDD architecture, multi-database, and pluggable AI agents.",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "health", "description": "Service health and metrics"},
        {"name": "agents", "description": "AI agent invocation (REST, WebSocket, SSE)"},
        {"name": "data", "description": "File upload and data streaming"},
        {"name": "dashboard", "description": "AI usage intelligence dashboard"},
        {"name": "webhooks", "description": "External event ingestion"},
        {"name": "metrics", "description": "Prometheus-style metrics"},
    ],
)

# Middleware — CORS, security headers, rate limiting, logging
setup_middleware(app, settings)

# Routers
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.agents import router as agents_router
from app.api.v1.endpoints.data import router as data_router
from app.api.v1.endpoints.stream import router as stream_router
from app.api.v1.endpoints.webhooks import router as webhooks_router
from app.api.v1.endpoints.metrics import router as metrics_router
from app.api.v1.endpoints.data_stream import router as data_stream_router
from app.api.v1.endpoints.autonomous import router as autonomous_router
from app.api.v1.endpoints.dashboard import router as dashboard_router
from app.api.v1.endpoints.auth import router as auth_router

app.include_router(health_router, prefix="/api/v1", tags=["health"])
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(agents_router, prefix="/api/v1/agents", tags=["agents"])
app.include_router(stream_router, prefix="/api/v1/agents", tags=["agents"])
app.include_router(data_router, prefix="/api/v1/data", tags=["data"])
app.include_router(dashboard_router, prefix="/api/v1/dashboard", tags=["dashboard"])
app.include_router(webhooks_router, prefix="/api/v1/webhooks", tags=["webhooks"])
app.include_router(metrics_router, prefix="/api/v1", tags=["metrics"])
app.include_router(data_stream_router, prefix="/api/v1/data", tags=["data"])
app.include_router(autonomous_router, prefix="/api/v1/autonomous", tags=["autonomous"])

# GraphQL (optional — uncomment to enable GraphiQL at /graphql)
# from app.api.graphql import graphql_router
# app.include_router(graphql_router, prefix="/graphql")
