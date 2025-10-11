"""Analytics domain events for tracking user journey and metrics."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from src.domain.value_objects.session_id import SessionId
from src.domain.value_objects.user_segment import UserSegment


def _generate_event_id() -> UUID:
    """Generate a new event ID."""
    return uuid4()


def _generate_timestamp() -> datetime:
    """Generate current UTC timestamp."""
    return datetime.now(UTC)


@dataclass(frozen=True)
class SessionStarted:
    """Event raised when a user session starts.

    Marks the beginning of a user's interaction session with the bot.
    """

    session_id: SessionId
    user_hash: str
    segment: UserSegment
    event_id: UUID = field(default_factory=_generate_event_id)
    occurred_at: datetime = field(default_factory=_generate_timestamp)


@dataclass(frozen=True)
class SessionEnded:
    """Event raised when a user session ends.

    Captures session completion with total duration.
    """

    session_id: SessionId
    user_hash: str
    duration_seconds: float
    event_id: UUID = field(default_factory=_generate_event_id)
    occurred_at: datetime = field(default_factory=_generate_timestamp)


@dataclass(frozen=True)
class FlowStarted:
    """Event raised when a user starts a conversation flow.

    Tracks the beginning of a specific flow within a session.
    """

    session_id: SessionId
    flow_id: str
    user_hash: str
    event_id: UUID = field(default_factory=_generate_event_id)
    occurred_at: datetime = field(default_factory=_generate_timestamp)


@dataclass(frozen=True)
class FlowCompleted:
    """Event raised when a user completes a conversation flow.

    Captures successful flow completion with duration.
    """

    session_id: SessionId
    flow_id: str
    user_hash: str
    duration_seconds: float
    event_id: UUID = field(default_factory=_generate_event_id)
    occurred_at: datetime = field(default_factory=_generate_timestamp)


@dataclass(frozen=True)
class FlowAbandoned:
    """Event raised when a user abandons a flow before completion.

    Tracks which step the user was on when they abandoned the flow.
    """

    session_id: SessionId
    flow_id: str
    user_hash: str
    abandoned_at_step: str
    event_id: UUID = field(default_factory=_generate_event_id)
    occurred_at: datetime = field(default_factory=_generate_timestamp)


@dataclass(frozen=True)
class FlowStepCompleted:
    """Event raised when a user completes a step in a flow.

    Tracks progress through individual flow steps.
    """

    session_id: SessionId
    flow_id: str
    step_id: str
    user_hash: str
    event_id: UUID = field(default_factory=_generate_event_id)
    occurred_at: datetime = field(default_factory=_generate_timestamp)
