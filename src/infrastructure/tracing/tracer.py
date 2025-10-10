"""OpenTelemetry tracer configuration and setup."""

from __future__ import annotations

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import ParentBasedTraceIdRatio

from src.infrastructure.config.settings import get_settings

SERVICE_NAME = "service.name"
SERVICE_VERSION = "service.version"


def setup_tracing() -> None:
    """Configure OpenTelemetry tracing with OTLP or console export."""
    settings = get_settings()

    if not settings.otel_enabled:
        return

    resource = Resource(
        attributes={
            SERVICE_NAME: settings.otel_service_name,
            SERVICE_VERSION: "0.1.0",
        }
    )

    sampler = ParentBasedTraceIdRatio(settings.otel_traces_sample_rate)
    provider = TracerProvider(resource=resource, sampler=sampler)

    if settings.otel_exporter_endpoint:
        otlp_exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_endpoint)
        batch_processor = BatchSpanProcessor(otlp_exporter)
        provider.add_span_processor(batch_processor)
    # Note: If no exporter endpoint configured, tracing is enabled but spans
    # are not exported anywhere. This allows instrumentation to work without
    # cluttering logs. To see traces, configure OTEL_EXPORTER_ENDPOINT in .env

    trace.set_tracer_provider(provider)


def shutdown_tracing() -> None:
    """Shutdown tracing and flush any pending spans."""
    provider = trace.get_tracer_provider()
    if hasattr(provider, "shutdown"):
        provider.shutdown()  # type: ignore[attr-defined]


def get_tracer(name: str) -> trace.Tracer:  # type: ignore[no-any-unimported]
    """Get tracer for instrumenting code.

    Args:
        name: Tracer name (usually __name__ of module)

    Returns:
        Tracer instance
    """
    return trace.get_tracer(name)
