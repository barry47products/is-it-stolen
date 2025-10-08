"""Conversation states for WhatsApp bot."""

from enum import Enum


class ConversationState(str, Enum):
    """States for conversation flow.

    **New simplified states (preferred):**
    - IDLE: Initial state
    - MAIN_MENU: User sees main menu options
    - ACTIVE_FLOW: Generic state for any running configuration-driven flow
    - COMPLETE: Flow completed successfully
    - CANCELLED: Flow cancelled by user

    **Legacy states (deprecated, will be removed in future version):**
    - CHECKING_* states: Legacy check flow states
    - REPORTING_* states: Legacy report flow states
    """

    # Initial states
    IDLE = "idle"
    MAIN_MENU = "main_menu"

    # Active flow (configuration-driven) - PREFERRED
    ACTIVE_FLOW = "active_flow"

    # Legacy check item flow states (DEPRECATED - use ACTIVE_FLOW instead)
    CHECKING_CATEGORY = "checking_category"
    CHECKING_DESCRIPTION = "checking_description"
    CHECKING_LOCATION = "checking_location"
    CHECKING_RESULTS = "checking_results"

    # Legacy report item flow states (DEPRECATED - use ACTIVE_FLOW instead)
    REPORTING_CATEGORY = "reporting_category"
    REPORTING_DESCRIPTION = "reporting_description"
    REPORTING_LOCATION = "reporting_location"
    REPORTING_DATE = "reporting_date"
    REPORTING_IMAGE = "reporting_image"
    REPORTING_CONFIRM = "reporting_confirm"

    # Terminal states
    COMPLETE = "complete"
    CANCELLED = "cancelled"


# Allowed state transitions
STATE_TRANSITIONS: dict[ConversationState, list[ConversationState]] = {
    ConversationState.IDLE: [
        ConversationState.MAIN_MENU,
    ],
    ConversationState.MAIN_MENU: [
        ConversationState.ACTIVE_FLOW,  # Preferred: config-driven flows
        ConversationState.CHECKING_CATEGORY,  # Legacy fallback
        ConversationState.REPORTING_CATEGORY,  # Legacy fallback
        ConversationState.CANCELLED,
    ],
    # New config-driven flow state (PREFERRED)
    ConversationState.ACTIVE_FLOW: [
        ConversationState.ACTIVE_FLOW,  # Can stay in ACTIVE_FLOW while processing
        ConversationState.COMPLETE,
        ConversationState.CANCELLED,
    ],
    # Legacy check flow states (DEPRECATED)
    ConversationState.CHECKING_CATEGORY: [
        ConversationState.CHECKING_DESCRIPTION,
        ConversationState.MAIN_MENU,
        ConversationState.CANCELLED,
    ],
    ConversationState.CHECKING_DESCRIPTION: [
        ConversationState.CHECKING_LOCATION,
        ConversationState.CHECKING_CATEGORY,
        ConversationState.CANCELLED,
    ],
    ConversationState.CHECKING_LOCATION: [
        ConversationState.CHECKING_RESULTS,
        ConversationState.CHECKING_DESCRIPTION,
        ConversationState.CANCELLED,
    ],
    ConversationState.CHECKING_RESULTS: [
        ConversationState.MAIN_MENU,
        ConversationState.COMPLETE,
        ConversationState.CANCELLED,
    ],
    # Legacy report flow states (DEPRECATED)
    ConversationState.REPORTING_CATEGORY: [
        ConversationState.REPORTING_DESCRIPTION,
        ConversationState.MAIN_MENU,
        ConversationState.CANCELLED,
    ],
    ConversationState.REPORTING_DESCRIPTION: [
        ConversationState.REPORTING_LOCATION,
        ConversationState.REPORTING_CATEGORY,
        ConversationState.CANCELLED,
    ],
    ConversationState.REPORTING_LOCATION: [
        ConversationState.REPORTING_DATE,
        ConversationState.REPORTING_DESCRIPTION,
        ConversationState.CANCELLED,
    ],
    ConversationState.REPORTING_DATE: [
        ConversationState.REPORTING_IMAGE,
        ConversationState.REPORTING_LOCATION,
        ConversationState.CANCELLED,
    ],
    ConversationState.REPORTING_IMAGE: [
        ConversationState.REPORTING_CONFIRM,
        ConversationState.REPORTING_DATE,
        ConversationState.CANCELLED,
    ],
    ConversationState.REPORTING_CONFIRM: [
        ConversationState.COMPLETE,
        ConversationState.REPORTING_IMAGE,
        ConversationState.CANCELLED,
    ],
    # Terminal states
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
