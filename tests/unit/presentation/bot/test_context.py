"""Tests for conversation context."""

from datetime import datetime

import pytest

from src.presentation.bot.context import ConversationContext
from src.presentation.bot.states import ConversationState


@pytest.mark.unit
class TestConversationContext:
    """Test conversation context data structure."""

    def test_creates_context_with_defaults(self) -> None:
        """Test creating context with default values."""
        # Arrange
        phone_number = "+1234567890"

        # Act
        context = ConversationContext(phone_number=phone_number)

        # Assert
        assert context.phone_number == phone_number
        assert context.state == ConversationState.IDLE
        assert context.data == {}
        assert isinstance(context.created_at, datetime)
        assert isinstance(context.updated_at, datetime)

    def test_creates_context_with_custom_state(self) -> None:
        """Test creating context with custom initial state."""
        # Arrange
        phone_number = "+1234567890"
        state = ConversationState.MAIN_MENU

        # Act
        context = ConversationContext(phone_number=phone_number, state=state)

        # Assert
        assert context.state == ConversationState.MAIN_MENU

    def test_creates_context_with_data(self) -> None:
        """Test creating context with initial data."""
        # Arrange
        phone_number = "+1234567890"
        data: dict[str, object] = {"action": "check", "category": "bicycle"}

        # Act
        context = ConversationContext(phone_number=phone_number, data=data)

        # Assert
        assert context.data == data

    def test_updates_timestamp_on_modification(self) -> None:
        """Test that updated_at changes when context is modified."""
        # Arrange
        context = ConversationContext(phone_number="+1234567890")
        original_updated_at = context.updated_at

        # Act
        updated_context = context.with_state(ConversationState.MAIN_MENU)

        # Assert
        assert updated_context.updated_at > original_updated_at

    def test_with_state_returns_new_instance(self) -> None:
        """Test with_state returns new instance (immutable pattern)."""
        # Arrange
        context = ConversationContext(phone_number="+1234567890")

        # Act
        new_context = context.with_state(ConversationState.MAIN_MENU)

        # Assert
        assert new_context is not context
        assert context.state == ConversationState.IDLE
        assert new_context.state == ConversationState.MAIN_MENU

    def test_with_data_returns_new_instance(self) -> None:
        """Test with_data returns new instance."""
        # Arrange
        context = ConversationContext(phone_number="+1234567890")

        # Act
        new_context = context.with_data({"key": "value"})

        # Assert
        assert new_context is not context
        assert context.data == {}
        assert new_context.data == {"key": "value"}

    def test_with_data_merges_existing_data(self) -> None:
        """Test with_data merges with existing data."""
        # Arrange
        context = ConversationContext(
            phone_number="+1234567890", data={"existing": "value"}
        )

        # Act
        new_context = context.with_data({"new": "data"})

        # Assert
        assert new_context.data == {"existing": "value", "new": "data"}

    def test_to_dict_serializes_context(self) -> None:
        """Test to_dict serializes context to dictionary."""
        # Arrange
        context = ConversationContext(
            phone_number="+1234567890",
            state=ConversationState.MAIN_MENU,
            data={"action": "check"},
        )

        # Act
        result = context.to_dict()

        # Assert
        assert result["phone_number"] == "+1234567890"
        assert result["state"] == "main_menu"
        assert result["data"] == {"action": "check"}
        assert "created_at" in result
        assert "updated_at" in result

    def test_from_dict_deserializes_context(self) -> None:
        """Test from_dict creates context from dictionary."""
        # Arrange
        data: dict[str, object] = {
            "phone_number": "+1234567890",
            "state": "main_menu",
            "data": {"action": "check"},
            "created_at": "2025-01-01T00:00:00+00:00",
            "updated_at": "2025-01-01T00:01:00+00:00",
        }

        # Act
        context = ConversationContext.from_dict(data)

        # Assert
        assert context.phone_number == "+1234567890"
        assert context.state == ConversationState.MAIN_MENU
        assert context.data == {"action": "check"}
        assert isinstance(context.created_at, datetime)
        assert isinstance(context.updated_at, datetime)

    def test_is_active_returns_true_for_non_terminal_states(self) -> None:
        """Test is_active returns True for active conversation."""
        # Arrange
        context = ConversationContext(
            phone_number="+1234567890", state=ConversationState.MAIN_MENU
        )

        # Act & Assert
        assert context.is_active()

    def test_is_active_returns_false_for_complete_state(self) -> None:
        """Test is_active returns False for complete state."""
        # Arrange
        context = ConversationContext(
            phone_number="+1234567890", state=ConversationState.COMPLETE
        )

        # Act & Assert
        assert not context.is_active()

    def test_is_active_returns_false_for_cancelled_state(self) -> None:
        """Test is_active returns False for cancelled state."""
        # Arrange
        context = ConversationContext(
            phone_number="+1234567890", state=ConversationState.CANCELLED
        )

        # Act & Assert
        assert not context.is_active()
