"""Tests for conversation states."""

import pytest

from src.presentation.bot.states import ConversationState, is_valid_transition


@pytest.mark.unit
class TestConversationStates:
    """Test conversation state enum."""

    def test_all_states_are_strings(self) -> None:
        """Test that all states are string values."""
        for state in ConversationState:
            assert isinstance(state.value, str)

    def test_idle_state_exists(self) -> None:
        """Test IDLE state exists."""
        assert ConversationState.IDLE.value == "idle"

    def test_main_menu_state_exists(self) -> None:
        """Test MAIN_MENU state exists."""
        assert ConversationState.MAIN_MENU.value == "main_menu"

    def test_terminal_states_exist(self) -> None:
        """Test terminal states exist."""
        assert ConversationState.COMPLETE.value == "complete"
        assert ConversationState.CANCELLED.value == "cancelled"


@pytest.mark.unit
class TestStateTransitions:
    """Test state transition validation."""

    def test_idle_can_transition_to_main_menu(self) -> None:
        """Test IDLE can transition to MAIN_MENU."""
        assert is_valid_transition(ConversationState.IDLE, ConversationState.MAIN_MENU)

    def test_idle_cannot_transition_to_checking(self) -> None:
        """Test IDLE cannot skip to CHECKING_CATEGORY."""
        assert not is_valid_transition(
            ConversationState.IDLE, ConversationState.CHECKING_CATEGORY
        )

    def test_main_menu_can_transition_to_checking(self) -> None:
        """Test MAIN_MENU can transition to checking flow."""
        assert is_valid_transition(
            ConversationState.MAIN_MENU, ConversationState.CHECKING_CATEGORY
        )

    def test_main_menu_can_transition_to_reporting(self) -> None:
        """Test MAIN_MENU can transition to reporting flow."""
        assert is_valid_transition(
            ConversationState.MAIN_MENU, ConversationState.REPORTING_CATEGORY
        )

    def test_can_cancel_from_any_active_state(self) -> None:
        """Test user can cancel from any non-terminal state."""
        cancellable_states = [
            ConversationState.MAIN_MENU,
            ConversationState.CHECKING_CATEGORY,
            ConversationState.REPORTING_CATEGORY,
        ]

        for state in cancellable_states:
            assert is_valid_transition(state, ConversationState.CANCELLED)

    def test_cannot_transition_from_complete(self) -> None:
        """Test COMPLETE is a terminal state."""
        assert not is_valid_transition(
            ConversationState.COMPLETE, ConversationState.MAIN_MENU
        )

    def test_cannot_transition_from_cancelled(self) -> None:
        """Test CANCELLED is a terminal state."""
        assert not is_valid_transition(
            ConversationState.CANCELLED, ConversationState.MAIN_MENU
        )

    def test_can_go_back_in_checking_flow(self) -> None:
        """Test user can navigate backwards in checking flow."""
        # From description back to category
        assert is_valid_transition(
            ConversationState.CHECKING_DESCRIPTION,
            ConversationState.CHECKING_CATEGORY,
        )

        # From location back to description
        assert is_valid_transition(
            ConversationState.CHECKING_LOCATION,
            ConversationState.CHECKING_DESCRIPTION,
        )

    def test_can_go_back_in_reporting_flow(self) -> None:
        """Test user can navigate backwards in reporting flow."""
        # From description back to category
        assert is_valid_transition(
            ConversationState.REPORTING_DESCRIPTION,
            ConversationState.REPORTING_CATEGORY,
        )

        # From location back to description
        assert is_valid_transition(
            ConversationState.REPORTING_LOCATION,
            ConversationState.REPORTING_DESCRIPTION,
        )
