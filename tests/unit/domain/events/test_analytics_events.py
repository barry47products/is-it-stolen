"""Unit tests for analytics domain events."""

from datetime import UTC, datetime

from src.domain.events.analytics_events import (
    FlowAbandoned,
    FlowCompleted,
    FlowStarted,
    FlowStepCompleted,
    SessionEnded,
    SessionStarted,
)
from src.domain.value_objects.session_id import SessionId
from src.domain.value_objects.user_segment import UserSegment


class TestSessionStarted:
    """Test suite for SessionStarted event."""

    def test_creates_session_started_event(self) -> None:
        """Test creating SessionStarted event."""
        # Arrange
        session_id = SessionId.generate()
        user_hash = "abc123"
        segment = UserSegment.FIRST_TIME
        occurred_at = datetime.now(UTC)

        # Act
        event = SessionStarted(
            session_id=session_id,
            user_hash=user_hash,
            segment=segment,
            occurred_at=occurred_at,
        )

        # Assert
        assert event.session_id == session_id
        assert event.user_hash == user_hash
        assert event.segment == segment
        assert event.occurred_at == occurred_at
        assert event.event_id is not None

    def test_event_is_immutable(self) -> None:
        """Test that SessionStarted event is immutable."""
        # Arrange
        event = SessionStarted(
            session_id=SessionId.generate(),
            user_hash="abc123",
            segment=UserSegment.FIRST_TIME,
        )

        # Act & Assert
        try:
            event.user_hash = "xyz789"  # type: ignore[misc]
            raise AssertionError("Should not allow mutation")
        except Exception:
            pass  # Expected


class TestSessionEnded:
    """Test suite for SessionEnded event."""

    def test_creates_session_ended_event(self) -> None:
        """Test creating SessionEnded event."""
        # Arrange
        session_id = SessionId.generate()
        user_hash = "abc123"
        duration_seconds = 300.0

        # Act
        event = SessionEnded(
            session_id=session_id,
            user_hash=user_hash,
            duration_seconds=duration_seconds,
        )

        # Assert
        assert event.session_id == session_id
        assert event.user_hash == user_hash
        assert event.duration_seconds == 300.0


class TestFlowStarted:
    """Test suite for FlowStarted event."""

    def test_creates_flow_started_event(self) -> None:
        """Test creating FlowStarted event."""
        # Arrange
        session_id = SessionId.generate()
        flow_id = "report_item"
        user_hash = "abc123"

        # Act
        event = FlowStarted(
            session_id=session_id,
            flow_id=flow_id,
            user_hash=user_hash,
        )

        # Assert
        assert event.session_id == session_id
        assert event.flow_id == flow_id
        assert event.user_hash == user_hash


class TestFlowCompleted:
    """Test suite for FlowCompleted event."""

    def test_creates_flow_completed_event(self) -> None:
        """Test creating FlowCompleted event."""
        # Arrange
        session_id = SessionId.generate()
        flow_id = "report_item"
        user_hash = "abc123"
        duration_seconds = 120.5

        # Act
        event = FlowCompleted(
            session_id=session_id,
            flow_id=flow_id,
            user_hash=user_hash,
            duration_seconds=duration_seconds,
        )

        # Assert
        assert event.session_id == session_id
        assert event.flow_id == flow_id
        assert event.duration_seconds == 120.5


class TestFlowAbandoned:
    """Test suite for FlowAbandoned event."""

    def test_creates_flow_abandoned_event(self) -> None:
        """Test creating FlowAbandoned event."""
        # Arrange
        session_id = SessionId.generate()
        flow_id = "check_item"
        user_hash = "abc123"
        abandoned_at_step = "location"

        # Act
        event = FlowAbandoned(
            session_id=session_id,
            flow_id=flow_id,
            user_hash=user_hash,
            abandoned_at_step=abandoned_at_step,
        )

        # Assert
        assert event.session_id == session_id
        assert event.flow_id == flow_id
        assert event.abandoned_at_step == "location"


class TestFlowStepCompleted:
    """Test suite for FlowStepCompleted event."""

    def test_creates_flow_step_completed_event(self) -> None:
        """Test creating FlowStepCompleted event."""
        # Arrange
        session_id = SessionId.generate()
        flow_id = "report_item"
        step_id = "category"
        user_hash = "abc123"

        # Act
        event = FlowStepCompleted(
            session_id=session_id,
            flow_id=flow_id,
            step_id=step_id,
            user_hash=user_hash,
        )

        # Assert
        assert event.session_id == session_id
        assert event.flow_id == flow_id
        assert event.step_id == step_id


class TestAllAnalyticsEvents:
    """Tests that apply to all analytics events."""

    def test_all_events_have_unique_event_ids(self) -> None:
        """Test that each event gets unique ID."""
        # Arrange & Act
        event1 = SessionStarted(
            session_id=SessionId.generate(),
            user_hash="abc",
            segment=UserSegment.FIRST_TIME,
        )
        event2 = SessionStarted(
            session_id=SessionId.generate(),
            user_hash="abc",
            segment=UserSegment.FIRST_TIME,
        )

        # Assert
        assert event1.event_id != event2.event_id

    def test_all_events_have_occurred_at_timestamp(self) -> None:
        """Test that all events have occurred_at."""
        # Arrange & Act
        events = [
            SessionStarted(
                session_id=SessionId.generate(),
                user_hash="abc",
                segment=UserSegment.FIRST_TIME,
            ),
            SessionEnded(
                session_id=SessionId.generate(),
                user_hash="abc",
                duration_seconds=100.0,
            ),
            FlowStarted(
                session_id=SessionId.generate(),
                flow_id="report_item",
                user_hash="abc",
            ),
        ]

        # Assert
        for event in events:
            assert hasattr(event, "occurred_at")
            assert isinstance(event.occurred_at, datetime)
            assert event.occurred_at.tzinfo is not None
