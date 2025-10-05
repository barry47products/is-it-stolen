"""Conversation context for managing user conversation state."""

from dataclasses import dataclass, field
from datetime import UTC, datetime

from src.presentation.bot.states import ConversationState


@dataclass(frozen=True)
class ConversationContext:
    """Immutable conversation context for a user.

    Stores the current state and accumulated data for a conversation.
    Uses immutable pattern - modifications return new instances.
    """

    phone_number: str
    state: ConversationState = ConversationState.IDLE
    data: dict[str, object] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def with_state(self, new_state: ConversationState) -> "ConversationContext":
        """Return new context with updated state.

        Args:
            new_state: New conversation state

        Returns:
            New ConversationContext instance with updated state
        """
        return ConversationContext(
            phone_number=self.phone_number,
            state=new_state,
            data=self.data,
            created_at=self.created_at,
            updated_at=datetime.now(UTC),
        )

    def with_data(self, new_data: dict[str, object]) -> "ConversationContext":
        """Return new context with merged data.

        Args:
            new_data: Data to merge with existing data

        Returns:
            New ConversationContext instance with merged data
        """
        merged_data = {**self.data, **new_data}
        return ConversationContext(
            phone_number=self.phone_number,
            state=self.state,
            data=merged_data,
            created_at=self.created_at,
            updated_at=datetime.now(UTC),
        )

    def is_active(self) -> bool:
        """Check if conversation is still active.

        Returns:
            True if conversation is active (not complete or cancelled)
        """
        terminal_states = {ConversationState.COMPLETE, ConversationState.CANCELLED}
        return self.state not in terminal_states

    def to_dict(self) -> dict[str, object]:
        """Serialize context to dictionary for storage.

        Returns:
            Dictionary representation of context
        """
        return {
            "phone_number": self.phone_number,
            "state": self.state.value,
            "data": self.data,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "ConversationContext":
        """Deserialize context from dictionary.

        Args:
            data: Dictionary representation of context

        Returns:
            ConversationContext instance
        """
        return cls(
            phone_number=str(data["phone_number"]),
            state=ConversationState(data["state"]),
            data=dict(data.get("data", {})),  # type: ignore[call-overload,arg-type]
            created_at=datetime.fromisoformat(str(data["created_at"])),
            updated_at=datetime.fromisoformat(str(data["updated_at"])),
        )
