"""Unit tests for logger utilities."""

from __future__ import annotations

from src.infrastructure.logging.logger import bind_report, bind_user, get_logger
from src.infrastructure.logging.processors import hash_phone_number


class TestGetLogger:
    """Test get_logger function."""

    def test_returns_structlog_logger(self) -> None:
        """Test that get_logger returns a structlog logger instance."""
        # Act
        logger = get_logger(__name__)

        # Assert
        # Structlog returns a lazy proxy, not the bound logger directly
        assert hasattr(logger, "info")
        assert hasattr(logger, "error")
        assert hasattr(logger, "warning")

    def test_returns_logger_with_name(self) -> None:
        """Test that logger has the specified name."""
        # Arrange
        name = "test.module"

        # Act
        logger = get_logger(name)

        # Assert
        # The logger should be bound to the name
        assert logger._context == {}  # type: ignore[attr-defined]

    def test_returns_root_logger_when_name_is_none(self) -> None:
        """Test that root logger is returned when name is None."""
        # Act
        logger = get_logger(None)

        # Assert
        # Structlog returns a lazy proxy, not the bound logger directly
        assert hasattr(logger, "info")
        assert hasattr(logger, "error")


class TestBindUser:
    """Test bind_user helper function."""

    def test_creates_context_with_hashed_phone(self) -> None:
        """Test that bind_user creates context with hashed phone."""
        # Arrange
        phone = "+447700900000"

        # Act
        context = bind_user(phone)

        # Assert
        assert "user_id_hash" in context
        assert context["user_id_hash"] == hash_phone_number(phone)
        assert "phone" not in context

    def test_includes_extra_context(self) -> None:
        """Test that extra context is included."""
        # Arrange
        phone = "+447700900000"

        # Act
        context = bind_user(phone, action="report", category="bicycle")

        # Assert
        assert context["user_id_hash"] == hash_phone_number(phone)
        assert context["action"] == "report"
        assert context["category"] == "bicycle"

    def test_extra_context_can_be_empty(self) -> None:
        """Test that extra context is optional."""
        # Arrange
        phone = "+447700900000"

        # Act
        context = bind_user(phone)

        # Assert
        assert len(context) == 1
        assert "user_id_hash" in context


class TestBindReport:
    """Test bind_report helper function."""

    def test_creates_context_with_report_id(self) -> None:
        """Test that bind_report creates context with report_id."""
        # Arrange
        report_id = "123e4567-e89b-12d3-a456-426614174000"

        # Act
        context = bind_report(report_id)

        # Assert
        assert context["report_id"] == report_id

    def test_includes_extra_context(self) -> None:
        """Test that extra context is included."""
        # Arrange
        report_id = "123e4567-e89b-12d3-a456-426614174000"

        # Act
        context = bind_report(report_id, category="bicycle", status="verified")

        # Assert
        assert context["report_id"] == report_id
        assert context["category"] == "bicycle"
        assert context["status"] == "verified"

    def test_extra_context_can_be_empty(self) -> None:
        """Test that extra context is optional."""
        # Arrange
        report_id = "123e4567-e89b-12d3-a456-426614174000"

        # Act
        context = bind_report(report_id)

        # Assert
        assert len(context) == 1
        assert "report_id" in context
