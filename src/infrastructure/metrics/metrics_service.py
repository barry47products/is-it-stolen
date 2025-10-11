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

# Analytics metrics
SESSIONS_STARTED = Counter(
    "sessions_started_total",
    "Total number of user sessions started",
    ["user_segment"],
)
SESSIONS_ENDED = Counter(
    "sessions_ended_total",
    "Total number of user sessions ended",
)
SESSION_DURATION = Histogram(
    "session_duration_seconds",
    "Session duration in seconds",
    buckets=(10, 30, 60, 120, 300, 600, 1200, 1800, 3600),
)
FLOW_STARTED = Counter(
    "flow_started_total",
    "Total number of flows started",
    ["flow_id", "user_segment"],
)
FLOW_COMPLETED = Counter(
    "flow_completed_total",
    "Total number of flows completed",
    ["flow_id"],
)
FLOW_ABANDONED = Counter(
    "flow_abandoned_total",
    "Total number of flows abandoned",
    ["flow_id", "step_id"],
)
FLOW_STEP_COMPLETED = Counter(
    "flow_step_completed_total",
    "Total number of flow steps completed",
    ["flow_id", "step_id"],
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

    # Analytics metrics tracking
    def track_session_started(self, user_segment: str) -> None:
        """Track session start with user segment.

        Args:
            user_segment: User segment (first_time, returning, power_user)
        """
        SESSIONS_STARTED.labels(user_segment=user_segment).inc()

    def track_session_ended(self, duration_seconds: float) -> None:
        """Track session end with duration.

        Args:
            duration_seconds: Session duration in seconds
        """
        SESSIONS_ENDED.inc()
        SESSION_DURATION.observe(duration_seconds)

    def track_flow_started(self, flow_id: str, user_segment: str) -> None:
        """Track flow start.

        Args:
            flow_id: Flow identifier
            user_segment: User segment
        """
        FLOW_STARTED.labels(flow_id=flow_id, user_segment=user_segment).inc()

    def track_flow_completed(self, flow_id: str) -> None:
        """Track flow completion.

        Args:
            flow_id: Flow identifier
        """
        FLOW_COMPLETED.labels(flow_id=flow_id).inc()

    def track_flow_abandoned(self, flow_id: str, step_id: str) -> None:
        """Track flow abandonment.

        Args:
            flow_id: Flow identifier
            step_id: Step where flow was abandoned
        """
        FLOW_ABANDONED.labels(flow_id=flow_id, step_id=step_id).inc()

    def track_step_completed(self, flow_id: str, step_id: str) -> None:
        """Track flow step completion.

        Args:
            flow_id: Flow identifier
            step_id: Step identifier
        """
        FLOW_STEP_COMPLETED.labels(flow_id=flow_id, step_id=step_id).inc()


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
