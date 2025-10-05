"""Message router for handling state-based message routing."""

from src.presentation.bot.context import ConversationContext
from src.presentation.bot.message_parser import MessageParser
from src.presentation.bot.state_machine import ConversationStateMachine
from src.presentation.bot.states import ConversationState


class MessageRouter:
    """Routes messages based on conversation state."""

    def __init__(
        self, state_machine: ConversationStateMachine, parser: MessageParser
    ) -> None:
        """Initialize message router.

        Args:
            state_machine: Conversation state machine
            parser: Message parser for extracting data
        """
        self.state_machine = state_machine
        self.parser = parser

    async def route_message(
        self, phone_number: str, message_text: str
    ) -> dict[str, str]:
        """Route message based on current conversation state.

        Args:
            phone_number: User's phone number
            message_text: Message text from user

        Returns:
            Response dictionary with reply and state
        """
        # Get current context
        context = await self.state_machine.get_or_create(phone_number)

        # Handle global commands
        if message_text.lower().strip() in ["cancel", "quit", "exit", "stop"]:
            await self.state_machine.cancel(context)
            return {
                "reply": "Conversation cancelled. Send any message to start again.",
                "state": ConversationState.CANCELLED.value,
            }

        # Route based on current state
        if context.state == ConversationState.IDLE:
            return await self._handle_idle(context)
        elif context.state == ConversationState.MAIN_MENU:
            return await self._handle_main_menu(context, message_text)
        elif context.state == ConversationState.CHECKING_CATEGORY:
            return await self._handle_checking_category(context, message_text)
        elif context.state == ConversationState.CHECKING_DESCRIPTION:
            return await self._handle_checking_description(context, message_text)
        elif context.state == ConversationState.CHECKING_LOCATION:
            return await self._handle_checking_location(context, message_text)
        elif context.state == ConversationState.REPORTING_CATEGORY:
            return await self._handle_reporting_category(context, message_text)
        elif context.state == ConversationState.REPORTING_DESCRIPTION:
            return await self._handle_reporting_description(context, message_text)
        elif context.state == ConversationState.REPORTING_LOCATION:
            return await self._handle_reporting_location(context, message_text)
        else:
            # Terminal state or unknown - reset to idle
            context = await self.state_machine.get_or_create(phone_number)
            return await self._handle_idle(context)

    async def _handle_idle(self, context: ConversationContext) -> dict[str, str]:
        """Handle IDLE state - transition to main menu."""
        new_context = await self.state_machine.transition(
            context, ConversationState.MAIN_MENU
        )
        return {
            "reply": (
                "👋 Welcome to Is It Stolen!\n\n"
                "What would you like to do?\n"
                "1️⃣ Check if an item is stolen\n"
                "2️⃣ Report a stolen item\n\n"
                "Reply with 1 or 2, or type 'cancel' to exit."
            ),
            "state": new_context.state.value,
        }

    async def _handle_main_menu(
        self, context: ConversationContext, message_text: str
    ) -> dict[str, str]:
        """Handle MAIN_MENU state - route to check or report flow."""
        choice = message_text.strip()

        if choice in ["1", "check", "Check"]:
            new_context = await self.state_machine.transition(
                context, ConversationState.CHECKING_CATEGORY
            )
            return {
                "reply": (
                    "🔍 Check if stolen\n\n"
                    "What type of item do you want to check?\n"
                    "Examples: bike, phone, laptop, car\n\n"
                    "Type 'cancel' to go back."
                ),
                "state": new_context.state.value,
            }
        elif choice in ["2", "report", "Report"]:
            new_context = await self.state_machine.transition(
                context, ConversationState.REPORTING_CATEGORY
            )
            return {
                "reply": (
                    "📝 Report stolen item\n\n"
                    "What type of item was stolen?\n"
                    "Examples: bike, phone, laptop, car\n\n"
                    "Type 'cancel' to go back."
                ),
                "state": new_context.state.value,
            }
        else:
            return {
                "reply": (
                    "Please choose an option:\n"
                    "1️⃣ Check if an item is stolen\n"
                    "2️⃣ Report a stolen item\n\n"
                    "Type 'cancel' to exit."
                ),
                "state": context.state.value,
            }

    async def _handle_checking_category(
        self, context: ConversationContext, message_text: str
    ) -> dict[str, str]:
        """Handle CHECKING_CATEGORY state."""
        category = self.parser.parse_category(message_text)

        if category:
            # Store category and move to description
            new_context = await self.state_machine.update_data(
                context, {"category": category.value}
            )
            new_context = await self.state_machine.transition(
                new_context, ConversationState.CHECKING_DESCRIPTION
            )
            return {
                "reply": (
                    f"✅ Got it, checking for: {category.value}\n\n"
                    "Please describe the item (brand, model, color, etc.):\n"
                    "Example: Red Trek mountain bike, serial ABC123"
                ),
                "state": new_context.state.value,
            }
        else:
            return {
                "reply": (
                    "❌ I didn't recognize that item type.\n\n"
                    "Please try again with: bike, phone, laptop, or car"
                ),
                "state": context.state.value,
            }

    async def _handle_checking_description(
        self, context: ConversationContext, message_text: str
    ) -> dict[str, str]:
        """Handle CHECKING_DESCRIPTION state."""
        # Extract brand/model
        brand_model = self.parser.extract_brand_model(message_text)

        # Store description and move to location
        new_context = await self.state_machine.update_data(
            context, {"description": message_text, "brand_model": brand_model}
        )
        new_context = await self.state_machine.transition(
            new_context, ConversationState.CHECKING_LOCATION
        )

        return {
            "reply": (
                "📍 Where was it last seen or stolen?\n\n"
                "You can either:\n"
                "• Type a location (e.g., 'Main Street, downtown')\n"
                "• Send your current location\n"
                "• Type 'skip' if you don't know"
            ),
            "state": new_context.state.value,
        }

    async def _handle_checking_location(
        self, context: ConversationContext, message_text: str
    ) -> dict[str, str]:
        """Handle CHECKING_LOCATION state."""
        if message_text.lower().strip() == "skip":
            location = None
        else:
            location = self.parser.parse_location_text(message_text)

        # Store location and complete
        new_context = await self.state_machine.update_data(
            context, {"location": location}
        )
        await self.state_machine.complete(new_context)

        # TODO: Actually query the database with the collected data
        # For now, just acknowledge
        return {
            "reply": (
                "🔍 Searching for matches...\n\n"
                "No stolen items found matching your description.\n\n"
                "Send any message to start a new search."
            ),
            "state": ConversationState.COMPLETE.value,
        }

    async def _handle_reporting_category(
        self, context: ConversationContext, message_text: str
    ) -> dict[str, str]:
        """Handle REPORTING_CATEGORY state."""
        category = self.parser.parse_category(message_text)

        if category:
            new_context = await self.state_machine.update_data(
                context, {"category": category.value}
            )
            new_context = await self.state_machine.transition(
                new_context, ConversationState.REPORTING_DESCRIPTION
            )
            return {
                "reply": (
                    f"✅ Reporting stolen: {category.value}\n\n"
                    "Please describe the item in detail:\n"
                    "Include: brand, model, color, serial number, any unique features"
                ),
                "state": new_context.state.value,
            }
        else:
            return {
                "reply": (
                    "❌ I didn't recognize that item type.\n\n"
                    "Please try again with: bike, phone, laptop, or car"
                ),
                "state": context.state.value,
            }

    async def _handle_reporting_description(
        self, context: ConversationContext, message_text: str
    ) -> dict[str, str]:
        """Handle REPORTING_DESCRIPTION state."""
        brand_model = self.parser.extract_brand_model(message_text)

        new_context = await self.state_machine.update_data(
            context, {"description": message_text, "brand_model": brand_model}
        )
        new_context = await self.state_machine.transition(
            new_context, ConversationState.REPORTING_LOCATION
        )

        return {
            "reply": (
                "📍 Where was it stolen?\n\n"
                "You can either:\n"
                "• Type the location\n"
                "• Send your location\n"
                "• Type 'unknown' if you're not sure"
            ),
            "state": new_context.state.value,
        }

    async def _handle_reporting_location(
        self, context: ConversationContext, message_text: str
    ) -> dict[str, str]:
        """Handle REPORTING_LOCATION state."""
        if message_text.lower().strip() == "unknown":
            location = None
        else:
            location = self.parser.parse_location_text(message_text)

        new_context = await self.state_machine.update_data(
            context, {"location": location}
        )
        await self.state_machine.complete(new_context)

        # TODO: Actually save to database with the collected data
        return {
            "reply": (
                "✅ Thank you for reporting!\n\n"
                "Your stolen item has been recorded.\n"
                "We'll notify you if there are any matches.\n\n"
                "Send any message to make another report."
            ),
            "state": ConversationState.COMPLETE.value,
        }
