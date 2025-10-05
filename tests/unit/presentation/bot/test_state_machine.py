"""Tests for conversation state machine."""

from unittest.mock import AsyncMock

import pytest

from src.presentation.bot.context import ConversationContext
from src.presentation.bot.exceptions import InvalidStateTransitionError
from src.presentation.bot.state_machine import ConversationStateMachine
from src.presentation.bot.states import ConversationState
from src.presentation.bot.storage import ConversationStorage


@pytest.mark.unit
class TestConversationStateMachine:
    """Test conversation state machine."""

    @pytest.fixture
    def mock_storage(self) -> AsyncMock:
        """Create mock storage."""
        storage = AsyncMock(spec=ConversationStorage)
        storage.get = AsyncMock(return_value=None)
        storage.save = AsyncMock()
        storage.delete = AsyncMock()
        return storage

    @pytest.fixture
    def state_machine(self, mock_storage: AsyncMock) -> ConversationStateMachine:
        """Create state machine with mock storage."""
        return ConversationStateMachine(storage=mock_storage)

    @pytest.mark.asyncio
    async def test_get_or_create_returns_new_context_when_none_exists(
        self, state_machine: ConversationStateMachine, mock_storage: AsyncMock
    ) -> None:
        """Test get_or_create returns new context if none exists."""
        # Arrange
        phone_number = "+1234567890"
        mock_storage.get.return_value = None

        # Act
        context = await state_machine.get_or_create(phone_number)

        # Assert
        assert context.phone_number == phone_number
        assert context.state == ConversationState.IDLE
        mock_storage.get.assert_called_once_with(phone_number)

    @pytest.mark.asyncio
    async def test_get_or_create_returns_existing_context(
        self, state_machine: ConversationStateMachine, mock_storage: AsyncMock
    ) -> None:
        """Test get_or_create returns existing context."""
        # Arrange
        phone_number = "+1234567890"
        existing_context = ConversationContext(
            phone_number=phone_number, state=ConversationState.MAIN_MENU
        )
        mock_storage.get.return_value = existing_context

        # Act
        context = await state_machine.get_or_create(phone_number)

        # Assert
        assert context == existing_context
        assert context.state == ConversationState.MAIN_MENU

    @pytest.mark.asyncio
    async def test_transition_updates_state_and_saves(
        self, state_machine: ConversationStateMachine, mock_storage: AsyncMock
    ) -> None:
        """Test transition updates state and saves to storage."""
        # Arrange
        context = ConversationContext(phone_number="+1234567890")

        # Act
        new_context = await state_machine.transition(
            context, ConversationState.MAIN_MENU
        )

        # Assert
        assert new_context.state == ConversationState.MAIN_MENU
        mock_storage.save.assert_called_once()
        saved_context = mock_storage.save.call_args[0][0]
        assert saved_context.state == ConversationState.MAIN_MENU

    @pytest.mark.asyncio
    async def test_transition_raises_error_for_invalid_transition(
        self, state_machine: ConversationStateMachine, mock_storage: AsyncMock
    ) -> None:
        """Test transition raises error for invalid state transition."""
        # Arrange
        context = ConversationContext(
            phone_number="+1234567890", state=ConversationState.IDLE
        )

        # Act & Assert
        with pytest.raises(InvalidStateTransitionError) as exc_info:
            await state_machine.transition(context, ConversationState.CHECKING_CATEGORY)

        assert "idle" in str(exc_info.value).lower()
        assert "checking_category" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_update_data_merges_data_and_saves(
        self, state_machine: ConversationStateMachine, mock_storage: AsyncMock
    ) -> None:
        """Test update_data merges data and saves."""
        # Arrange
        context = ConversationContext(
            phone_number="+1234567890", data={"existing": "value"}
        )

        # Act
        new_context = await state_machine.update_data(context, {"new": "data"})

        # Assert
        assert new_context.data == {"existing": "value", "new": "data"}
        mock_storage.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_reset_clears_context_from_storage(
        self, state_machine: ConversationStateMachine, mock_storage: AsyncMock
    ) -> None:
        """Test reset deletes context from storage."""
        # Arrange
        phone_number = "+1234567890"

        # Act
        await state_machine.reset(phone_number)

        # Assert
        mock_storage.delete.assert_called_once_with(phone_number)

    @pytest.mark.asyncio
    async def test_cancel_transitions_to_cancelled_and_deletes(
        self, state_machine: ConversationStateMachine, mock_storage: AsyncMock
    ) -> None:
        """Test cancel transitions to CANCELLED state and deletes context."""
        # Arrange
        context = ConversationContext(
            phone_number="+1234567890", state=ConversationState.MAIN_MENU
        )

        # Act
        new_context = await state_machine.cancel(context)

        # Assert
        assert new_context.state == ConversationState.CANCELLED
        mock_storage.delete.assert_called_once_with("+1234567890")

    @pytest.mark.asyncio
    async def test_complete_transitions_to_complete_and_deletes(
        self, state_machine: ConversationStateMachine, mock_storage: AsyncMock
    ) -> None:
        """Test complete transitions to COMPLETE state and deletes context."""
        # Arrange
        context = ConversationContext(
            phone_number="+1234567890", state=ConversationState.REPORTING_CONFIRM
        )

        # Act
        new_context = await state_machine.complete(context)

        # Assert
        assert new_context.state == ConversationState.COMPLETE
        mock_storage.delete.assert_called_once_with("+1234567890")
