"""Conversation state machine for managing conversation flow."""

from src.presentation.bot.context import ConversationContext
from src.presentation.bot.exceptions import InvalidStateTransitionError
from src.presentation.bot.states import ConversationState, is_valid_transition
from src.presentation.bot.storage import ConversationStorage


class ConversationStateMachine:
    """State machine for managing conversation state transitions."""

    def __init__(self, storage: ConversationStorage) -> None:
        """Initialize state machine with storage.

        Args:
            storage: Storage implementation for conversation contexts
        """
        self.storage = storage

    async def get_or_create(self, phone_number: str) -> ConversationContext:
        """Get existing conversation or create new one.

        Args:
            phone_number: User's phone number

        Returns:
            ConversationContext for the user
        """
        context = await self.storage.get(phone_number)

        if context is None:
            # Create new conversation starting in IDLE state
            context = ConversationContext(phone_number=phone_number)

        return context

    async def transition(
        self, context: ConversationContext, new_state: ConversationState
    ) -> ConversationContext:
        """Transition conversation to new state.

        Args:
            context: Current conversation context
            new_state: State to transition to

        Returns:
            Updated conversation context

        Raises:
            InvalidStateTransitionError: If transition is not allowed
        """
        # Validate transition
        if not is_valid_transition(context.state, new_state):
            raise InvalidStateTransitionError(
                current_state=context.state.value,
                attempted_state=new_state.value,
            )

        # Create new context with updated state
        new_context = context.with_state(new_state)

        # Save to storage
        await self.storage.save(new_context)

        return new_context

    async def update_data(
        self, context: ConversationContext, data: dict[str, object]
    ) -> ConversationContext:
        """Update conversation data.

        Args:
            context: Current conversation context
            data: Data to merge with existing data

        Returns:
            Updated conversation context
        """
        new_context = context.with_data(data)
        await self.storage.save(new_context)
        return new_context

    async def reset(self, phone_number: str) -> None:
        """Reset conversation by deleting context.

        Args:
            phone_number: User's phone number
        """
        await self.storage.delete(phone_number)

    async def cancel(self, context: ConversationContext) -> ConversationContext:
        """Cancel conversation.

        Args:
            context: Current conversation context

        Returns:
            Context with CANCELLED state
        """
        # Transition to cancelled state
        cancelled_context = context.with_state(ConversationState.CANCELLED)

        # Delete from storage (no need to keep cancelled conversations)
        await self.storage.delete(context.phone_number)

        return cancelled_context

    async def complete(self, context: ConversationContext) -> ConversationContext:
        """Complete conversation.

        Args:
            context: Current conversation context

        Returns:
            Context with COMPLETE state
        """
        # Transition to complete state
        complete_context = context.with_state(ConversationState.COMPLETE)

        # Delete from storage (no need to keep completed conversations)
        await self.storage.delete(context.phone_number)

        return complete_context
