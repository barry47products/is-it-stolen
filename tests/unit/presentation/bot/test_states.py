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

    def test_has_simplified_and_legacy_states(self) -> None:
        """Test that state machine has simplified states plus legacy states."""
        states = list(ConversationState)
        # 5 simplified + 10 legacy (deprecated) = 15 total states
        # (IDLE, MAIN_MENU, ACTIVE_FLOW, COMPLETE, CANCELLED + 10 legacy states)
        assert len(states) == 15

    def test_idle_state_exists(self) -> None:
        """Test IDLE state exists."""
        assert ConversationState.IDLE.value == "idle"

    def test_main_menu_state_exists(self) -> None:
        """Test MAIN_MENU state exists."""
        assert ConversationState.MAIN_MENU.value == "main_menu"

    def test_active_flow_state_exists(self) -> None:
        """Test ACTIVE_FLOW state exists."""
        assert ConversationState.ACTIVE_FLOW.value == "active_flow"

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

    def test_idle_cannot_transition_to_active_flow(self) -> None:
        """Test IDLE cannot skip directly to ACTIVE_FLOW."""
        assert not is_valid_transition(
            ConversationState.IDLE, ConversationState.ACTIVE_FLOW
        )

    def test_main_menu_can_transition_to_active_flow(self) -> None:
        """Test MAIN_MENU can transition to ACTIVE_FLOW."""
        assert is_valid_transition(
            ConversationState.MAIN_MENU, ConversationState.ACTIVE_FLOW
        )

    def test_main_menu_can_cancel(self) -> None:
        """Test MAIN_MENU can transition to CANCELLED."""
        assert is_valid_transition(
            ConversationState.MAIN_MENU, ConversationState.CANCELLED
        )

    def test_active_flow_can_stay_in_active_flow(self) -> None:
        """Test ACTIVE_FLOW can transition to itself (multi-step flows)."""
        assert is_valid_transition(
            ConversationState.ACTIVE_FLOW, ConversationState.ACTIVE_FLOW
        )

    def test_active_flow_can_complete(self) -> None:
        """Test ACTIVE_FLOW can transition to COMPLETE."""
        assert is_valid_transition(
            ConversationState.ACTIVE_FLOW, ConversationState.COMPLETE
        )

    def test_active_flow_can_cancel(self) -> None:
        """Test ACTIVE_FLOW can transition to CANCELLED."""
        assert is_valid_transition(
            ConversationState.ACTIVE_FLOW, ConversationState.CANCELLED
        )

    def test_complete_can_restart(self) -> None:
        """Test COMPLETE can transition back to IDLE for new conversation."""
        assert is_valid_transition(ConversationState.COMPLETE, ConversationState.IDLE)

    def test_cancelled_can_restart(self) -> None:
        """Test CANCELLED can transition back to IDLE for new conversation."""
        assert is_valid_transition(ConversationState.CANCELLED, ConversationState.IDLE)

    def test_complete_cannot_transition_to_active_flow(self) -> None:
        """Test COMPLETE cannot directly transition to ACTIVE_FLOW."""
        assert not is_valid_transition(
            ConversationState.COMPLETE, ConversationState.ACTIVE_FLOW
        )

    def test_cancelled_cannot_transition_to_active_flow(self) -> None:
        """Test CANCELLED cannot directly transition to ACTIVE_FLOW."""
        assert not is_valid_transition(
            ConversationState.CANCELLED, ConversationState.ACTIVE_FLOW
        )
