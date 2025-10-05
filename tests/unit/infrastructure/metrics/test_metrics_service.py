"""Unit tests for metrics service."""

import pytest

from src.infrastructure.metrics.metrics_service import MetricsService


class TestMetricsService:
    """Test metrics service functionality."""

    @pytest.fixture
    def metrics_service(self) -> MetricsService:
        """Create metrics service for testing."""
        return MetricsService()

    def test_increment_messages_received(self, metrics_service: MetricsService) -> None:
        """Test incrementing messages received counter."""
        # Arrange
        initial_count = metrics_service.get_messages_received()

        # Act
        metrics_service.increment_messages_received()
        metrics_service.increment_messages_received()

        # Assert
        assert metrics_service.get_messages_received() == initial_count + 2

    def test_increment_messages_sent(self, metrics_service: MetricsService) -> None:
        """Test incrementing messages sent counter."""
        # Arrange
        initial_count = metrics_service.get_messages_sent()

        # Act
        metrics_service.increment_messages_sent()

        # Assert
        assert metrics_service.get_messages_sent() == initial_count + 1

    def test_increment_reports_created(self, metrics_service: MetricsService) -> None:
        """Test incrementing reports created counter."""
        # Arrange
        initial_count = metrics_service.get_reports_created()

        # Act
        metrics_service.increment_reports_created()
        metrics_service.increment_reports_created()
        metrics_service.increment_reports_created()

        # Assert
        assert metrics_service.get_reports_created() == initial_count + 3

    def test_increment_items_checked(self, metrics_service: MetricsService) -> None:
        """Test incrementing items checked counter."""
        # Arrange
        initial_count = metrics_service.get_items_checked()

        # Act
        metrics_service.increment_items_checked()

        # Assert
        assert metrics_service.get_items_checked() == initial_count + 1

    def test_record_response_time(self, metrics_service: MetricsService) -> None:
        """Test recording response time."""
        # Act
        metrics_service.record_response_time(0.123)
        metrics_service.record_response_time(0.456)

        # Assert
        avg_time = metrics_service.get_average_response_time()
        assert avg_time == pytest.approx(0.2895, rel=0.01)

    def test_track_active_user(self, metrics_service: MetricsService) -> None:
        """Test tracking active users."""
        # Act
        metrics_service.track_active_user("+1234567890")
        metrics_service.track_active_user("+1234567890")  # Same user
        metrics_service.track_active_user("+0987654321")  # Different user

        # Assert
        assert metrics_service.get_active_users_count() == 2

    def test_get_all_metrics(self, metrics_service: MetricsService) -> None:
        """Test getting all metrics as dict."""
        # Arrange
        metrics_service.increment_messages_received()
        metrics_service.increment_messages_sent()
        metrics_service.increment_reports_created()
        metrics_service.increment_items_checked()
        metrics_service.record_response_time(0.5)
        metrics_service.track_active_user("+1234567890")

        # Act
        metrics = metrics_service.get_all_metrics()

        # Assert
        assert metrics["messages_received"] == 1
        assert metrics["messages_sent"] == 1
        assert metrics["reports_created"] == 1
        assert metrics["items_checked"] == 1
        assert metrics["average_response_time"] == 0.5
        assert metrics["active_users"] == 1
        assert "timestamp" in metrics

    def test_reset_metrics(self, metrics_service: MetricsService) -> None:
        """Test resetting all metrics."""
        # Arrange
        metrics_service.increment_messages_received()
        metrics_service.increment_messages_sent()
        metrics_service.track_active_user("+1234567890")

        # Act
        metrics_service.reset_metrics()

        # Assert
        assert metrics_service.get_messages_received() == 0
        assert metrics_service.get_messages_sent() == 0
        assert metrics_service.get_active_users_count() == 0

    def test_metrics_service_is_singleton(self) -> None:
        """Test that MetricsService returns same instance."""
        from src.infrastructure.metrics.metrics_service import get_metrics_service

        # Act
        service1 = get_metrics_service()
        service2 = get_metrics_service()

        # Assert
        assert service1 is service2

    def test_response_time_average_with_no_data(
        self, metrics_service: MetricsService
    ) -> None:
        """Test average response time when no data recorded."""
        # Assert
        assert metrics_service.get_average_response_time() == 0.0

    def test_multiple_response_times_calculates_average(
        self, metrics_service: MetricsService
    ) -> None:
        """Test that multiple response times are averaged correctly."""
        # Act
        metrics_service.record_response_time(0.1)
        metrics_service.record_response_time(0.2)
        metrics_service.record_response_time(0.3)

        # Assert
        assert metrics_service.get_average_response_time() == pytest.approx(0.2)
