"""
OpenTelemetry tracing configuration for distributed tracing and observability.
"""
from typing import Optional
import os

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.trace import Span, Status, StatusCode

from app.config import get_settings

settings = get_settings()


def setup_tracing(app_name: str = "cognitude-api", environment: str = "development"):
    """
    Initialize OpenTelemetry tracing with OTLP export.
    
    Args:
        app_name: Name of the application for tracing
        environment: Environment (development, staging, production)
    """
    # Configure resource with service information
    resource = Resource.create({
        "service.name": app_name,
        "service.version": settings.APP_VERSION,
        "deployment.environment": environment,
        "service.instance.id": os.getenv("HOSTNAME", "localhost"),
    })
    
    # Initialize tracer provider
    provider = TracerProvider(resource=resource)
    
    # Configure exporters
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    
    if otlp_endpoint:
        # Production: Export to OTLP collector (Jaeger, Tempo, etc.)
        otlp_exporter = OTLPSpanExporter(
            endpoint=otlp_endpoint,
            insecure=os.getenv("OTEL_EXPORTER_OTLP_INSECURE", "false").lower() == "true"
        )
        span_processor = BatchSpanProcessor(otlp_exporter)
    else:
        # Development: Export to console
        console_exporter = ConsoleSpanExporter()
        span_processor = BatchSpanProcessor(console_exporter)
    
    provider.add_span_processor(span_processor)
    trace.set_tracer_provider(provider)
    
    return trace.get_tracer(app_name)


def instrument_app(app):
    """
    Instrument FastAPI application with OpenTelemetry.
    
    Args:
        app: FastAPI application instance
    """
    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)
    
    # Instrument SQLAlchemy (database)
    from app.database import engine
    SQLAlchemyInstrumentor().instrument(engine=engine)
    
    # Instrument Redis if available
    try:
        from app.services.redis_cache import redis_cache
        if redis_cache.available:
            RedisInstrumentor().instrument()
    except Exception:
        pass


def get_tracer(name: str):
    """
    Get a tracer instance for the given name.
    
    Args:
        name: Name of the tracer (usually __name__ of the module)
        
    Returns:
        Tracer instance
    """
    return trace.get_tracer(name)


def add_span_attributes(span: Span, attributes: dict):
    """
    Add attributes to a span safely.
    
    Args:
        span: The span to add attributes to
        attributes: Dictionary of attributes to add
    """
    if span and span.is_recording():
        for key, value in attributes.items():
            if value is not None:
                span.set_attribute(key, value)


def record_exception(span: Span, exception: Exception):
    """
    Record an exception on a span.
    
    Args:
        span: The span to record the exception on
        exception: The exception to record
    """
    if span and span.is_recording():
        span.record_exception(exception)
        span.set_status(Status(StatusCode.ERROR, str(exception)))


# Global tracer instance
tracer = get_tracer("cognitude")