"""Metrics service for tracking bot usage and performance."""

from datetime import UTC, datetime
from typing import Any

from prometheus_client import Counter, Gauge, Histogram

# Prometheus metrics - module level (shared across all instances)
MESSAGES_RECEIVED = Counter(
    "messages_received_total",
    "Total number of messages received from users",
)
MESSAGES_SENT = Counter(
    "messages_sent_total",
    "Total number of messages sent to users",
)
REPORTS_CREATED = Counter(
    "reports_created_total",
    "Total number of stolen item reports created",
)
ITEMS_CHECKED = Counter(
    "items_checked_total",
    "Total number of item check queries performed",
)
RESPONSE_TIME = Histogram(
    "response_time_seconds",
    "Response time for message processing in seconds",
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 10.0),
)
ACTIVE_USERS = Gauge(
    "active_users_total",
    "Number of unique active users",
)


class MetricsService:
    """Service for collecting and tracking bot metrics."""

    def __init__(self) -> None:
        """Initialize metrics service with zero counters."""
        self._messages_received = 0
        self._messages_sent = 0
        self._reports_created = 0
        self._items_checked = 0
        self._response_times: list[float] = []
        self._active_users: set[str] = set()

    def increment_messages_received(self) -> None:
        """Increment messages received counter."""
        self._messages_received += 1
        MESSAGES_RECEIVED.inc()

    def increment_messages_sent(self) -> None:
        """Increment messages sent counter."""
        self._messages_sent += 1
        MESSAGES_SENT.inc()

    def increment_reports_created(self) -> None:
        """Increment reports created counter."""
        self._reports_created += 1
        REPORTS_CREATED.inc()

    def increment_items_checked(self) -> None:
        """Increment items checked counter."""
        self._items_checked += 1
        ITEMS_CHECKED.inc()

    def record_response_time(self, response_time: float) -> None:
        """Record response time in seconds.

        Args:
            response_time: Response time in seconds
        """
        self._response_times.append(response_time)
        RESPONSE_TIME.observe(response_time)

    def track_active_user(self, phone_number: str) -> None:
        """Track active user by phone number.

        Args:
            phone_number: User's phone number
        """
        self._active_users.add(phone_number)
        ACTIVE_USERS.set(len(self._active_users))

    def get_messages_received(self) -> int:
        """Get total messages received count.

        Returns:
            Total messages received
        """
        return self._messages_received

    def get_messages_sent(self) -> int:
        """Get total messages sent count.

        Returns:
            Total messages sent
        """
        return self._messages_sent

    def get_reports_created(self) -> int:
        """Get total reports created count.

        Returns:
            Total reports created
        """
        return self._reports_created

    def get_items_checked(self) -> int:
        """Get total items checked count.

        Returns:
            Total items checked
        """
        return self._items_checked

    def get_average_response_time(self) -> float:
        """Get average response time in seconds.

        Returns:
            Average response time, or 0.0 if no data
        """
        if not self._response_times:
            return 0.0
        return sum(self._response_times) / len(self._response_times)

    def get_active_users_count(self) -> int:
        """Get count of active users.

        Returns:
            Number of unique active users
        """
        return len(self._active_users)

    def get_all_metrics(self) -> dict[str, Any]:
        """Get all metrics as a dictionary.

        Returns:
            Dictionary containing all current metrics
        """
        return {
            "messages_received": self._messages_received,
            "messages_sent": self._messages_sent,
            "reports_created": self._reports_created,
            "items_checked": self._items_checked,
            "average_response_time": self.get_average_response_time(),
            "active_users": self.get_active_users_count(),
            "timestamp": datetime.now(UTC).isoformat(),
        }

    def reset_metrics(self) -> None:
        """Reset all metrics to zero."""
        self._messages_received = 0
        self._messages_sent = 0
        self._reports_created = 0
        self._items_checked = 0
        self._response_times = []
        self._active_users = set()


# Singleton instance
_metrics_service: MetricsService | None = None


def get_metrics_service() -> MetricsService:
    """Get singleton metrics service instance.

    Returns:
        Shared MetricsService instance
    """
    global _metrics_service
    if _metrics_service is None:
        _metrics_service = MetricsService()
    return _metrics_service
