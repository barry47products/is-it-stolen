"""Tests for OpenTelemetry instrumentation."""

from unittest.mock import MagicMock, patch

from src.infrastructure.tracing.instrumentation import (
    instrument_all,
    instrument_database,
    instrument_http_client,
    instrument_redis,
)


class TestInstrumentDatabase:
    """Test database instrumentation."""

    @patch("src.infrastructure.tracing.instrumentation.SQLAlchemyInstrumentor")
    @patch("src.infrastructure.tracing.instrumentation.get_engine")
    def test_instrument_database_calls_instrumentor(
        self, mock_get_engine: MagicMock, mock_instrumentor: MagicMock
    ) -> None:
        """Should instrument SQLAlchemy with database engine."""
        # Arrange
        mock_engine = MagicMock()
        mock_get_engine.return_value = mock_engine
        mock_instance = MagicMock()
        mock_instrumentor.return_value = mock_instance

        # Act
        instrument_database()

        # Assert
        mock_get_engine.assert_called_once()
        mock_instrumentor.assert_called_once()
        mock_instance.instrument.assert_called_once_with(engine=mock_engine)


class TestInstrumentHttpClient:
    """Test HTTP client instrumentation."""

    @patch("src.infrastructure.tracing.instrumentation.HTTPXClientInstrumentor")
    def test_instrument_http_client_calls_instrumentor(
        self, mock_instrumentor: MagicMock
    ) -> None:
        """Should instrument httpx HTTP client."""
        # Arrange
        mock_instance = MagicMock()
        mock_instrumentor.return_value = mock_instance

        # Act
        instrument_http_client()

        # Assert
        mock_instrumentor.assert_called_once()
        mock_instance.instrument.assert_called_once()


class TestInstrumentRedis:
    """Test Redis instrumentation."""

    @patch("src.infrastructure.tracing.instrumentation.RedisInstrumentor")
    def test_instrument_redis_calls_instrumentor(
        self, mock_instrumentor: MagicMock
    ) -> None:
        """Should instrument Redis operations."""
        # Arrange
        mock_instance = MagicMock()
        mock_instrumentor.return_value = mock_instance

        # Act
        instrument_redis()

        # Assert
        mock_instrumentor.assert_called_once()
        mock_instance.instrument.assert_called_once()


class TestInstrumentAll:
    """Test instrumenting all libraries."""

    @patch("src.infrastructure.tracing.instrumentation.instrument_redis")
    @patch("src.infrastructure.tracing.instrumentation.instrument_http_client")
    @patch("src.infrastructure.tracing.instrumentation.instrument_database")
    def test_instrument_all_calls_all_instrumentors(
        self,
        mock_db: MagicMock,
        mock_http: MagicMock,
        mock_redis: MagicMock,
    ) -> None:
        """Should call all instrumentation functions."""
        # Act
        instrument_all()

        # Assert
        mock_db.assert_called_once()
        mock_http.assert_called_once()
        mock_redis.assert_called_once()
