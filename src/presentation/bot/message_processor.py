"""Message processor for handling incoming WhatsApp messages."""

from src.infrastructure.whatsapp.client import WhatsAppClient
from src.presentation.bot.message_parser import MessageParser
from src.presentation.bot.message_router import MessageRouter
from src.presentation.bot.state_machine import ConversationStateMachine


class MessageProcessor:
    """Process incoming WhatsApp messages through conversation state machine."""

    def __init__(
        self,
        state_machine: ConversationStateMachine,
        whatsapp_client: WhatsAppClient,
    ) -> None:
        """Initialize message processor.

        Args:
            state_machine: Conversation state machine for managing flow
            whatsapp_client: WhatsApp client for sending responses
        """
        self.state_machine = state_machine
        self.whatsapp_client = whatsapp_client
        self.parser = MessageParser()
        self.router = MessageRouter(state_machine, self.parser)

    async def process_message(
        self, phone_number: str, message_text: str
    ) -> dict[str, str]:
        """Process incoming message and return response.

        Args:
            phone_number: User's phone number
            message_text: Text of the message

        Returns:
            Response dictionary with reply text and state
        """
        # Route message through state machine
        response = await self.router.route_message(phone_number, message_text)

        # Send response via WhatsApp
        await self.whatsapp_client.send_text_message(
            to=phone_number, text=response["reply"]
        )

        return response
