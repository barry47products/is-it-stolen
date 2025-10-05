"""Exceptions for conversation state machine."""


class ConversationError(Exception):
    """Base exception for conversation errors."""

    pass


class InvalidStateTransitionError(ConversationError):
    """Raised when an invalid state transition is attempted."""

    def __init__(self, current_state: str, attempted_state: str) -> None:
        """Initialize with current and attempted states.

        Args:
            current_state: Current conversation state
            attempted_state: State that was attempted to transition to
        """
        self.current_state = current_state
        self.attempted_state = attempted_state
        super().__init__(
            f"Invalid state transition from '{current_state}' to '{attempted_state}'"
        )
