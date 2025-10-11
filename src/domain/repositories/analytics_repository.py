"""Repository interfaces for analytics data."""

from abc import ABC, abstractmethod
from datetime import datetime

from src.domain.entities.user_session import UserSession
from src.domain.events.analytics_events import (
    FlowAbandoned,
    FlowCompleted,
    FlowStarted,
    FlowStepCompleted,
    SessionEnded,
    SessionStarted,
)
from src.domain.value_objects.metric_type import MetricType
from src.domain.value_objects.session_id import SessionId

# Type alias for all analytics events
AnalyticsEvent = (
    SessionStarted
    | SessionEnded
    | FlowStarted
    | FlowCompleted
    | FlowAbandoned
    | FlowStepCompleted
)


class IAnalyticsEventRepository(ABC):
    """Repository interface for storing and retrieving analytics events.

    This interface defines operations for persisting analytics events
    without depending on any specific storage implementation.
    """

    @abstractmethod
    async def save_event(self, event: AnalyticsEvent) -> None:
        """Save an analytics event.

        Args:
            event: Analytics event to persist
        """
        ...

    @abstractmethod
    async def get_events_by_type(
        self, metric_type: MetricType, start_date: datetime, end_date: datetime
    ) -> list[AnalyticsEvent]:
        """Get events by type within date range.

        Args:
            metric_type: Type of metric to retrieve
            start_date: Start of date range
            end_date: End of date range

        Returns:
            List of matching events
        """
        ...

    @abstractmethod
    async def get_events_by_user(
        self, user_hash: str, start_date: datetime, end_date: datetime
    ) -> list[AnalyticsEvent]:
        """Get all events for a specific user.

        Args:
            user_hash: Hashed user identifier
            start_date: Start of date range
            end_date: End of date range

        Returns:
            List of user's events
        """
        ...

    @abstractmethod
    async def count_events_by_type(
        self, metric_type: MetricType, start_date: datetime, end_date: datetime
    ) -> int:
        """Count events of specific type in date range.

        Args:
            metric_type: Type of metric to count
            start_date: Start of date range
            end_date: End of date range

        Returns:
            Count of matching events
        """
        ...


class ISessionRepository(ABC):
    """Repository interface for user session management.

    Manages active and historical user sessions.
    """

    @abstractmethod
    async def save_session(self, session: UserSession) -> None:
        """Save or update a user session.

        Args:
            session: Session to persist
        """
        ...

    @abstractmethod
    async def get_session(self, session_id: SessionId) -> UserSession | None:
        """Get session by ID.

        Args:
            session_id: Session identifier

        Returns:
            Session if found, None otherwise
        """
        ...

    @abstractmethod
    async def get_active_session(self, user_hash: str) -> UserSession | None:
        """Get active session for user.

        Args:
            user_hash: Hashed user identifier

        Returns:
            Active session if exists, None otherwise
        """
        ...

    @abstractmethod
    async def get_user_sessions(
        self, user_hash: str, limit: int = 10
    ) -> list[UserSession]:
        """Get recent sessions for user.

        Args:
            user_hash: Hashed user identifier
            limit: Maximum number of sessions to return

        Returns:
            List of user's recent sessions
        """
        ...

    @abstractmethod
    async def count_user_sessions(self, user_hash: str) -> int:
        """Count total sessions for user.

        Args:
            user_hash: Hashed user identifier

        Returns:
            Total number of sessions
        """
        ...
