"""UserSession entity for tracking user interaction sessions."""

from dataclasses import dataclass, field
from datetime import datetime

from src.domain.value_objects.session_id import SessionId
from src.domain.value_objects.user_segment import UserSegment


@dataclass
class UserSession:
    """Entity representing a user's interaction session with the bot.

    A session tracks all user interactions from start to end, including
    which flows were used and the user's segment classification.
    """

    session_id: SessionId
    user_hash: str
    started_at: datetime
    segment: UserSegment
    ended_at: datetime | None = None
    flows_used: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate session data."""
        if self.ended_at and self.ended_at <= self.started_at:
            raise ValueError("ended_at must be after started_at")

    def is_active(self) -> bool:
        """Check if session is currently active.

        Returns:
            True if session has not ended yet
        """
        return self.ended_at is None

    def calculate_duration(self) -> float | None:
        """Calculate session duration in seconds.

        Returns:
            Duration in seconds, or None if session still active
        """
        if self.ended_at is None:
            return None
        delta = self.ended_at - self.started_at
        return delta.total_seconds()

    def end_session(self, ended_at: datetime) -> None:
        """End the session.

        Args:
            ended_at: Timestamp when session ended

        Raises:
            ValueError: If session is already ended
        """
        if self.ended_at is not None:
            raise ValueError("Session already ended")
        self.ended_at = ended_at

    def add_flow(self, flow_id: str) -> None:
        """Add a flow to the session.

        Args:
            flow_id: Identifier of the flow

        Raises:
            ValueError: If session is ended
        """
        if not self.is_active():
            raise ValueError("Cannot add flow to ended session")
        self.flows_used.append(flow_id)

    def get_flow_count(self) -> int:
        """Get count of flows used in session.

        Returns:
            Number of flows used
        """
        return len(self.flows_used)

    def __eq__(self, other: object) -> bool:
        """Check equality based on session ID."""
        if not isinstance(other, UserSession):
            return False
        return self.session_id == other.session_id

    def __hash__(self) -> int:
        """Hash based on session ID."""
        return hash(self.session_id)
