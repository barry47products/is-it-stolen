"""Unit tests for SessionId value object."""

from uuid import UUID, uuid4

import pytest

from src.domain.value_objects.session_id import SessionId


class TestSessionId:
    """Test suite for SessionId value object."""

    def test_creates_valid_session_id_from_uuid(self) -> None:
        """Test creating SessionId from valid UUID."""
        # Arrange
        valid_uuid = uuid4()

        # Act
        session_id = SessionId(valid_uuid)

        # Assert
        assert session_id.value == valid_uuid
        assert isinstance(session_id.value, UUID)

    def test_creates_valid_session_id_from_string(self) -> None:
        """Test creating SessionId from valid UUID string."""
        # Arrange
        valid_uuid_str = "123e4567-e89b-12d3-a456-426614174000"

        # Act
        session_id = SessionId.from_string(valid_uuid_str)

        # Assert
        assert str(session_id.value) == valid_uuid_str

    def test_rejects_invalid_uuid_string(self) -> None:
        """Test that invalid UUID string raises ValueError."""
        # Arrange
        invalid_uuid = "not-a-valid-uuid"

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid UUID format"):
            SessionId.from_string(invalid_uuid)

    def test_session_id_is_immutable(self) -> None:
        """Test that SessionId is immutable."""
        # Arrange
        session_id = SessionId(uuid4())

        # Act & Assert
        with pytest.raises((AttributeError, TypeError)):  # FrozenInstanceError
            session_id.value = uuid4()  # type: ignore[misc]

    def test_session_ids_with_same_uuid_are_equal(self) -> None:
        """Test that SessionIds with same UUID are equal."""
        # Arrange
        uuid_value = uuid4()
        session_id1 = SessionId(uuid_value)
        session_id2 = SessionId(uuid_value)

        # Act & Assert
        assert session_id1 == session_id2
        assert hash(session_id1) == hash(session_id2)

    def test_session_ids_with_different_uuids_are_not_equal(self) -> None:
        """Test that SessionIds with different UUIDs are not equal."""
        # Arrange
        session_id1 = SessionId(uuid4())
        session_id2 = SessionId(uuid4())

        # Act & Assert
        assert session_id1 != session_id2

    def test_to_string_returns_uuid_string(self) -> None:
        """Test converting SessionId to string."""
        # Arrange
        uuid_value = uuid4()
        session_id = SessionId(uuid_value)

        # Act
        result = session_id.to_string()

        # Assert
        assert result == str(uuid_value)

    def test_generates_new_session_id(self) -> None:
        """Test generating new random SessionId."""
        # Act
        session_id1 = SessionId.generate()
        session_id2 = SessionId.generate()

        # Assert
        assert isinstance(session_id1, SessionId)
        assert isinstance(session_id2, SessionId)
        assert session_id1 != session_id2
