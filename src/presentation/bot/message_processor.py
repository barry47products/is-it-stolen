"""Message processor for handling incoming WhatsApp messages."""

import time

from src.infrastructure.cache.rate_limiter import RateLimiter, RateLimitExceeded
from src.infrastructure.metrics.metrics_service import get_metrics_service
from src.infrastructure.whatsapp.client import WhatsAppClient
from src.presentation.bot.error_handler import ErrorHandler
from src.presentation.bot.flow_engine import FlowEngine
from src.presentation.bot.message_parser import MessageParser
from src.presentation.bot.message_router import MessageRouter
from src.presentation.bot.state_machine import ConversationStateMachine


class MessageProcessor:
    """Process incoming WhatsApp messages through conversation state machine."""

    def __init__(
        self,
        state_machine: ConversationStateMachine,
        whatsapp_client: WhatsAppClient,
        flow_engine: FlowEngine | None = None,
        rate_limiter: RateLimiter | None = None,
        error_handler: ErrorHandler | None = None,
    ) -> None:
        """Initialize message processor.

        Args:
            state_machine: Conversation state machine for managing flow
            whatsapp_client: WhatsApp client for sending responses
            flow_engine: Flow engine for config-driven conversation flows
            rate_limiter: Optional rate limiter for preventing abuse
            error_handler: Optional error handler for user-friendly messages
        """
        self.state_machine = state_machine
        self.whatsapp_client = whatsapp_client
        self.rate_limiter = rate_limiter
        self.error_handler = error_handler or ErrorHandler()
        self.parser = MessageParser()
        self.router = MessageRouter(state_machine, self.parser, flow_engine=flow_engine)

    async def process_message(
        self, phone_number: str, message_text: str
    ) -> dict[str, str]:
        """Process incoming message and return response.

        Args:
            phone_number: User's phone number
            message_text: Text of the message

        Returns:
            Response dictionary with reply text and state

        Raises:
            RateLimitExceeded: If rate limit is exceeded (handled internally)
        """
        # Track metrics
        metrics = get_metrics_service()
        metrics.increment_messages_received()
        metrics.track_active_user(phone_number)

        # Start timing for response time
        start_time = time.time()

        # Check rate limit if limiter is configured
        if self.rate_limiter is not None:
            try:
                await self.rate_limiter.check_rate_limit(phone_number)
            except RateLimitExceeded as error:
                # Convert to user-friendly error and send
                error_message = self.error_handler.handle_error(error)
                await self.whatsapp_client.send_text_message(
                    to=phone_number, text=error_message
                )
                metrics.increment_messages_sent()
                return {"reply": error_message, "state": "rate_limited"}

        # Route message through state machine
        response = await self.router.route_message(phone_number, message_text)

        # Send response via WhatsApp (handle both text and interactive messages)
        reply = response["reply"]
        reply_text = ""  # For response dict

        if isinstance(reply, dict):
            # Interactive message - check type and send appropriately
            if reply.get("type") == "interactive":
                interactive_type = reply.get("interactive", {}).get("type")
                if interactive_type == "button":
                    # Send reply buttons
                    body = reply["interactive"]["body"]["text"]
                    buttons = [
                        {"id": btn["reply"]["id"], "title": btn["reply"]["title"]}
                        for btn in reply["interactive"]["action"]["buttons"]
                    ]
                    await self.whatsapp_client.send_reply_buttons(
                        to=phone_number, body=body, buttons=buttons
                    )
                    reply_text = body  # Use body text for response
                elif interactive_type == "list":
                    # Send list message
                    body = reply["interactive"]["body"]["text"]
                    button_text = reply["interactive"]["action"]["button"]
                    sections = reply["interactive"]["action"]["sections"]
                    header = reply["interactive"].get("header", {}).get("text")
                    await self.whatsapp_client.send_list_message(
                        to=phone_number,
                        body=body,
                        button_text=button_text,
                        sections=sections,
                        header=header,
                    )
                    reply_text = body  # Use body text for response
        else:
            # Text message
            await self.whatsapp_client.send_text_message(to=phone_number, text=reply)
            reply_text = reply

        # Track response sent and response time
        metrics.increment_messages_sent()
        response_time = time.time() - start_time
        metrics.record_response_time(response_time)

        # Return response with text version of reply for backward compatibility
        return {"reply": reply_text, "state": response["state"]}
