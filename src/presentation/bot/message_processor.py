"""Message processor for handling incoming WhatsApp messages."""

from src.presentation.bot.state_machine import ConversationStateMachine


class MessageProcessor:
    """Process incoming WhatsApp messages through conversation state machine."""

    def __init__(self, state_machine: ConversationStateMachine) -> None:
        """Initialize message processor.

        Args:
            state_machine: Conversation state machine for managing flow
        """
        self.state_machine = state_machine

    async def process_message(
        self, phone_number: str, message_text: str
    ) -> dict[str, str]:
        """Process incoming message and return response.

        Args:
            phone_number: User's phone number
            message_text: Text of the message

        Returns:
            Response dictionary with reply text
        """
        # Get or create conversation context
        context = await self.state_machine.get_or_create(phone_number)

        # For now, just acknowledge the message
        # In Issue #34 we'll implement the message routing logic
        return {
            "reply": f"Received: {message_text}",
            "state": context.state.value,
        }
