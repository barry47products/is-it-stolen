"""Conversation states for WhatsApp bot."""

from enum import Enum


class ConversationState(str, Enum):
    """States for conversation flow.

    All flows use the config-driven ACTIVE_FLOW pattern:
    - IDLE: Initial state
    - MAIN_MENU: User sees main menu options
    - ACTIVE_FLOW: Generic state for any running configuration-driven flow
    - COMPLETE: Flow completed successfully
    - CANCELLED: Flow cancelled by user
    """

    # Initial states
    IDLE = "idle"
    MAIN_MENU = "main_menu"

    # Active flow (configuration-driven)
    ACTIVE_FLOW = "active_flow"

    # Terminal states
    COMPLETE = "complete"
    CANCELLED = "cancelled"


# Allowed state transitions
STATE_TRANSITIONS: dict[ConversationState, list[ConversationState]] = {
    ConversationState.IDLE: [
        ConversationState.MAIN_MENU,
    ],
    ConversationState.MAIN_MENU: [
        ConversationState.ACTIVE_FLOW,
        ConversationState.CANCELLED,
    ],
    ConversationState.ACTIVE_FLOW: [
        ConversationState.ACTIVE_FLOW,  # Can stay in ACTIVE_FLOW while processing steps
        ConversationState.COMPLETE,
        ConversationState.CANCELLED,
    ],
    ConversationState.COMPLETE: [
        ConversationState.IDLE,  # Allow starting new conversation
    ],
    ConversationState.CANCELLED: [
        ConversationState.IDLE,  # Allow starting new conversation
    ],
}


def is_valid_transition(
    current: ConversationState, next_state: ConversationState
) -> bool:
    """Check if transition from current to next state is valid.

    Args:
        current: Current conversation state
        next_state: Proposed next state

    Returns:
        True if transition is valid, False otherwise
    """
    allowed = STATE_TRANSITIONS.get(current, [])
    return next_state in allowed
