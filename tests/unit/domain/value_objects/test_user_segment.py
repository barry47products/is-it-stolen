"""Unit tests for UserSegment enum."""

from src.domain.value_objects.user_segment import UserSegment


class TestUserSegment:
    """Test suite for UserSegment enum."""

    def test_has_first_time_segment(self) -> None:
        """Test UserSegment has FIRST_TIME."""
        # Act & Assert
        assert UserSegment.FIRST_TIME.value == "first_time"

    def test_has_returning_segment(self) -> None:
        """Test UserSegment has RETURNING."""
        # Act & Assert
        assert UserSegment.RETURNING.value == "returning"

    def test_has_power_user_segment(self) -> None:
        """Test UserSegment has POWER_USER."""
        # Act & Assert
        assert UserSegment.POWER_USER.value == "power_user"

    def test_all_segments_are_strings(self) -> None:
        """Test all segment values are strings."""
        # Act & Assert
        for segment in UserSegment:
            assert isinstance(segment.value, str)

    def test_segments_are_unique(self) -> None:
        """Test all segment values are unique."""
        # Arrange
        values = [s.value for s in UserSegment]

        # Act & Assert
        assert len(values) == len(set(values))
