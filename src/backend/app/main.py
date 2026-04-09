from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.container import Container
from app.middleware import setup_middleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.startup import validate_environment, log_startup_info

    log_startup_info()
    validate_environment()

    container = Container()
    await container.init()
    app.state.container = container

    yield

    await container.close()


app = FastAPI(
    title="Argus API",
    description="AI Usage Intelligence — security analysis for enterprise AI conversations.",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "health", "description": "Service health"},
        {"name": "agents", "description": "AI agent invocation"},
        {"name": "data", "description": "File upload and data streaming"},
        {"name": "dashboard", "description": "AI usage intelligence dashboard"},
        {"name": "auth", "description": "Authentication"},
        {"name": "slopsquatting", "description": "Typosquat / slopsquat detection"},
    ],
)

# Middleware
setup_middleware(app, settings)

# Routers
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.agents import router as agents_router
from app.api.v1.endpoints.data import router as data_router
from app.api.v1.endpoints.stream import router as stream_router
from app.api.v1.endpoints.slopsquatting import router as slopsquatting_router
from app.api.v1.endpoints.dashboard import router as dashboard_router
from app.api.v1.endpoints.auth import router as auth_router

app.include_router(health_router, prefix="/api/v1", tags=["health"])
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(agents_router, prefix="/api/v1/agents", tags=["agents"])
app.include_router(stream_router, prefix="/api/v1/agents", tags=["agents"])
app.include_router(data_router, prefix="/api/v1/data", tags=["data"])
app.include_router(dashboard_router, prefix="/api/v1/dashboard", tags=["dashboard"])
app.include_router(slopsquatting_router, prefix="/api/v1/slopsquatting", tags=["slopsquatting"])
