"""OpenTelemetry instrumentation — traces, metrics, spans.

Auto-instruments FastAPI, httpx, SQLAlchemy, and Redis.
Exports to Jaeger (traces) and Prometheus (metrics).

Enable with OTEL_ENABLED=true. Does nothing when disabled.
"""

import structlog
from app.config import settings

log = structlog.get_logger()


def setup_telemetry(app) -> None:
    """Initialize OpenTelemetry if enabled. Call from main.py lifespan."""
    if not settings.otel_enabled:
        return

    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    from opentelemetry.instrumentation.redis import RedisInstrumentor

    resource = Resource.create({
        "service.name": settings.otel_service_name,
        "service.version": "0.1.0",
        "deployment.environment": "development" if settings.debug else "production",
    })

    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    # Auto-instrument frameworks
    FastAPIInstrumentor.instrument_app(app)
    HTTPXClientInstrumentor().instrument()
    SQLAlchemyInstrumentor().instrument()
    RedisInstrumentor().instrument()

    log.info("otel_initialized", endpoint=settings.otel_exporter_endpoint, service=settings.otel_service_name)


def get_tracer(name: str = "hackathon"):
    """Get a tracer for manual span creation.

    Usage:
        tracer = get_tracer()
        with tracer.start_as_current_span("agent_call") as span:
            span.set_attribute("agent.framework", "anthropic")
            result = await invoke_agent(...)
            span.set_attribute("agent.response_length", len(result))
    """
    from opentelemetry import trace
    return trace.get_tracer(name)
