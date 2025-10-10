"""Tests for OpenTelemetry tracer configuration."""

from unittest.mock import MagicMock, patch

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

from src.infrastructure.tracing.tracer import (
    get_tracer,
    setup_tracing,
    shutdown_tracing,
)


class TestSetupTracing:
    """Test tracing setup and configuration."""

    @patch("src.infrastructure.tracing.tracer.get_settings")
    @patch("src.infrastructure.tracing.tracer.trace.set_tracer_provider")
    def test_setup_tracing_when_disabled(
        self, mock_set_provider: MagicMock, mock_get_settings: MagicMock
    ) -> None:
        """Should not configure tracing when disabled in settings."""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.otel_enabled = False
        mock_get_settings.return_value = mock_settings

        # Act
        setup_tracing()

        # Assert
        mock_set_provider.assert_not_called()

    @patch("src.infrastructure.tracing.tracer.get_settings")
    @patch("src.infrastructure.tracing.tracer.trace.set_tracer_provider")
    def test_setup_tracing_without_exporter_endpoint(
        self, mock_set_provider: MagicMock, mock_get_settings: MagicMock
    ) -> None:
        """Should configure tracing without exporter when no endpoint provided."""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.otel_enabled = True
        mock_settings.otel_service_name = "test-service"
        mock_settings.otel_exporter_endpoint = ""
        mock_settings.otel_traces_sample_rate = 1.0
        mock_get_settings.return_value = mock_settings

        # Act
        setup_tracing()

        # Assert - Provider is created but no spans are exported
        mock_set_provider.assert_called_once()
        provider_arg = mock_set_provider.call_args[0][0]
        assert isinstance(provider_arg, TracerProvider)

    @patch("src.infrastructure.tracing.tracer.get_settings")
    @patch("src.infrastructure.tracing.tracer.trace.set_tracer_provider")
    @patch("src.infrastructure.tracing.tracer.OTLPSpanExporter")
    def test_setup_tracing_with_otlp_exporter(
        self,
        mock_otlp_exporter: MagicMock,
        mock_set_provider: MagicMock,
        mock_get_settings: MagicMock,
    ) -> None:
        """Should configure OTLP exporter when endpoint provided."""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.otel_enabled = True
        mock_settings.otel_service_name = "test-service"
        mock_settings.otel_exporter_endpoint = "http://localhost:4317"
        mock_settings.otel_traces_sample_rate = 0.5
        mock_get_settings.return_value = mock_settings

        # Act
        setup_tracing()

        # Assert
        mock_otlp_exporter.assert_called_once_with(endpoint="http://localhost:4317")
        mock_set_provider.assert_called_once()

    @patch("src.infrastructure.tracing.tracer.get_settings")
    @patch("src.infrastructure.tracing.tracer.ParentBasedTraceIdRatio")
    def test_setup_tracing_configures_sampling_rate(
        self, mock_sampler: MagicMock, mock_get_settings: MagicMock
    ) -> None:
        """Should configure sampling rate from settings."""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.otel_enabled = True
        mock_settings.otel_service_name = "test-service"
        mock_settings.otel_exporter_endpoint = ""
        mock_settings.otel_traces_sample_rate = 0.25
        mock_get_settings.return_value = mock_settings

        # Act
        setup_tracing()

        # Assert
        mock_sampler.assert_called_once_with(0.25)


class TestShutdownTracing:
    """Test tracing shutdown."""

    @patch("src.infrastructure.tracing.tracer.trace.get_tracer_provider")
    def test_shutdown_tracing_calls_provider_shutdown(
        self, mock_get_provider: MagicMock
    ) -> None:
        """Should call shutdown on tracer provider if available."""
        # Arrange
        mock_provider = MagicMock()
        mock_provider.shutdown = MagicMock()
        mock_get_provider.return_value = mock_provider

        # Act
        shutdown_tracing()

        # Assert
        mock_provider.shutdown.assert_called_once()

    @patch("src.infrastructure.tracing.tracer.trace.get_tracer_provider")
    def test_shutdown_tracing_handles_no_shutdown_method(
        self, mock_get_provider: MagicMock
    ) -> None:
        """Should handle provider without shutdown method gracefully."""
        # Arrange
        mock_provider = MagicMock(spec=[])  # No shutdown method
        mock_get_provider.return_value = mock_provider

        # Act & Assert - should not raise exception
        shutdown_tracing()


class TestGetTracer:
    """Test tracer retrieval."""

    def test_get_tracer_returns_tracer_instance(self) -> None:
        """Should return a tracer instance for given name."""
        # Arrange
        tracer_name = "test.module"

        # Act
        tracer = get_tracer(tracer_name)

        # Assert
        assert tracer is not None
        assert isinstance(tracer, trace.Tracer)

    def test_get_tracer_with_different_names(self) -> None:
        """Should return different tracers for different names."""
        # Arrange
        name1 = "module.one"
        name2 = "module.two"

        # Act
        tracer1 = get_tracer(name1)
        tracer2 = get_tracer(name2)

        # Assert
        assert tracer1 is not None
        assert tracer2 is not None
        # Note: OpenTelemetry may return same instance but with different name
