"""Unit tests for UserSession entity."""

from datetime import UTC, datetime, timedelta

import pytest

from src.domain.entities.user_session import UserSession
from src.domain.value_objects.session_id import SessionId
from src.domain.value_objects.user_segment import UserSegment


class TestUserSession:
    """Test suite for UserSession entity."""

    def test_creates_new_session(self) -> None:
        """Test creating a new user session."""
        # Arrange
        session_id = SessionId.generate()
        user_hash = "abc123"
        started_at = datetime.now(UTC)

        # Act
        session = UserSession(
            session_id=session_id,
            user_hash=user_hash,
            started_at=started_at,
            segment=UserSegment.FIRST_TIME,
        )

        # Assert
        assert session.session_id == session_id
        assert session.user_hash == user_hash
        assert session.started_at == started_at
        assert session.ended_at is None
        assert session.segment == UserSegment.FIRST_TIME
        assert session.flows_used == []

    def test_calculates_session_duration_when_ended(self) -> None:
        """Test calculating session duration for ended session."""
        # Arrange
        started_at = datetime(2025, 10, 11, 10, 0, 0, tzinfo=UTC)
        ended_at = datetime(2025, 10, 11, 10, 15, 30, tzinfo=UTC)
        session = UserSession(
            session_id=SessionId.generate(),
            user_hash="abc123",
            started_at=started_at,
            ended_at=ended_at,
            segment=UserSegment.RETURNING,
        )

        # Act
        duration = session.calculate_duration()

        # Assert
        assert duration == 930.0  # 15 minutes 30 seconds = 930 seconds

    def test_calculates_session_duration_when_active(self) -> None:
        """Test calculating duration for active session returns None."""
        # Arrange
        session = UserSession(
            session_id=SessionId.generate(),
            user_hash="abc123",
            started_at=datetime.now(UTC),
            segment=UserSegment.FIRST_TIME,
        )

        # Act
        duration = session.calculate_duration()

        # Assert
        assert duration is None

    def test_is_active_returns_true_when_not_ended(self) -> None:
        """Test session is active when not ended."""
        # Arrange
        session = UserSession(
            session_id=SessionId.generate(),
            user_hash="abc123",
            started_at=datetime.now(UTC),
            segment=UserSegment.FIRST_TIME,
        )

        # Act & Assert
        assert session.is_active() is True

    def test_is_active_returns_false_when_ended(self) -> None:
        """Test session is not active when ended."""
        # Arrange
        started_at = datetime.now(UTC)
        ended_at = started_at + timedelta(seconds=1)
        session = UserSession(
            session_id=SessionId.generate(),
            user_hash="abc123",
            started_at=started_at,
            ended_at=ended_at,
            segment=UserSegment.FIRST_TIME,
        )

        # Act & Assert
        assert session.is_active() is False

    def test_end_session_sets_ended_at(self) -> None:
        """Test ending session sets ended_at timestamp."""
        # Arrange
        session = UserSession(
            session_id=SessionId.generate(),
            user_hash="abc123",
            started_at=datetime.now(UTC),
            segment=UserSegment.FIRST_TIME,
        )
        end_time = datetime.now(UTC) + timedelta(minutes=10)

        # Act
        session.end_session(end_time)

        # Assert
        assert session.ended_at == end_time
        assert session.is_active() is False

    def test_cannot_end_session_twice(self) -> None:
        """Test cannot end an already ended session."""
        # Arrange
        session = UserSession(
            session_id=SessionId.generate(),
            user_hash="abc123",
            started_at=datetime.now(UTC),
            segment=UserSegment.FIRST_TIME,
        )
        session.end_session(datetime.now(UTC))

        # Act & Assert
        with pytest.raises(ValueError, match="already ended"):
            session.end_session(datetime.now(UTC))

    def test_add_flow_to_session(self) -> None:
        """Test adding a flow to session."""
        # Arrange
        session = UserSession(
            session_id=SessionId.generate(),
            user_hash="abc123",
            started_at=datetime.now(UTC),
            segment=UserSegment.FIRST_TIME,
        )

        # Act
        session.add_flow("report_item")

        # Assert
        assert "report_item" in session.flows_used
        assert len(session.flows_used) == 1

    def test_add_multiple_flows_to_session(self) -> None:
        """Test adding multiple flows to session."""
        # Arrange
        session = UserSession(
            session_id=SessionId.generate(),
            user_hash="abc123",
            started_at=datetime.now(UTC),
            segment=UserSegment.FIRST_TIME,
        )

        # Act
        session.add_flow("report_item")
        session.add_flow("check_item")
        session.add_flow("contact_us")

        # Assert
        assert session.flows_used == ["report_item", "check_item", "contact_us"]
        assert len(session.flows_used) == 3

    def test_cannot_add_flow_to_ended_session(self) -> None:
        """Test cannot add flow to ended session."""
        # Arrange
        started_at = datetime.now(UTC)
        ended_at = started_at + timedelta(seconds=1)
        session = UserSession(
            session_id=SessionId.generate(),
            user_hash="abc123",
            started_at=started_at,
            ended_at=ended_at,
            segment=UserSegment.FIRST_TIME,
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Cannot add flow to ended session"):
            session.add_flow("report_item")

    def test_get_flow_count(self) -> None:
        """Test getting count of flows used in session."""
        # Arrange
        session = UserSession(
            session_id=SessionId.generate(),
            user_hash="abc123",
            started_at=datetime.now(UTC),
            segment=UserSegment.RETURNING,
        )
        session.add_flow("report_item")
        session.add_flow("check_item")

        # Act
        count = session.get_flow_count()

        # Assert
        assert count == 2

    def test_ended_at_must_be_after_started_at(self) -> None:
        """Test validation that ended_at must be after started_at."""
        # Arrange
        started_at = datetime(2025, 10, 11, 10, 0, 0, tzinfo=UTC)
        ended_at = datetime(2025, 10, 11, 9, 0, 0, tzinfo=UTC)  # Before started

        # Act & Assert
        with pytest.raises(ValueError, match="ended_at must be after started_at"):
            UserSession(
                session_id=SessionId.generate(),
                user_hash="abc123",
                started_at=started_at,
                ended_at=ended_at,
                segment=UserSegment.FIRST_TIME,
            )

    def test_sessions_with_same_id_are_equal(self) -> None:
        """Test sessions with same ID are equal."""
        # Arrange
        session_id = SessionId.generate()
        session1 = UserSession(
            session_id=session_id,
            user_hash="abc123",
            started_at=datetime.now(UTC),
            segment=UserSegment.FIRST_TIME,
        )
        session2 = UserSession(
            session_id=session_id,
            user_hash="abc123",
            started_at=datetime.now(UTC),
            segment=UserSegment.FIRST_TIME,
        )

        # Act & Assert
        assert session1 == session2

    def test_sessions_with_different_ids_are_not_equal(self) -> None:
        """Test sessions with different IDs are not equal."""
        # Arrange
        session1 = UserSession(
            session_id=SessionId.generate(),
            user_hash="abc123",
            started_at=datetime.now(UTC),
            segment=UserSegment.FIRST_TIME,
        )
        session2 = UserSession(
            session_id=SessionId.generate(),
            user_hash="abc123",
            started_at=datetime.now(UTC),
            segment=UserSegment.FIRST_TIME,
        )

        # Act & Assert
        assert session1 != session2

    def test_session_not_equal_to_non_session_object(self) -> None:
        """Test session is not equal to non-UserSession objects."""
        # Arrange
        session = UserSession(
            session_id=SessionId.generate(),
            user_hash="abc123",
            started_at=datetime.now(UTC),
            segment=UserSegment.FIRST_TIME,
        )

        # Act & Assert
        assert session != "not a session"
        assert session != 123
        assert session != None  # noqa: E711

    def test_session_hash_is_consistent(self) -> None:
        """Test that session hash is consistent for same session."""
        # Arrange
        session = UserSession(
            session_id=SessionId.generate(),
            user_hash="abc123",
            started_at=datetime.now(UTC),
            segment=UserSegment.FIRST_TIME,
        )

        # Act
        hash1 = hash(session)
        hash2 = hash(session)

        # Assert
        assert hash1 == hash2

    def test_sessions_with_same_id_have_same_hash(self) -> None:
        """Test sessions with same ID have same hash."""
        # Arrange
        session_id = SessionId.generate()
        session1 = UserSession(
            session_id=session_id,
            user_hash="abc123",
            started_at=datetime.now(UTC),
            segment=UserSegment.FIRST_TIME,
        )
        session2 = UserSession(
            session_id=session_id,
            user_hash="def456",
            started_at=datetime.now(UTC),
            segment=UserSegment.RETURNING,
        )

        # Act & Assert
        assert hash(session1) == hash(session2)
