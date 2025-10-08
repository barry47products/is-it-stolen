"""Message router for handling state-based message routing."""

import logging
from typing import TYPE_CHECKING, Any, cast

from src.application.commands.report_stolen_item import ReportStolenItemHandler
from src.application.queries.check_if_stolen import CheckIfStolenHandler
from src.infrastructure.geocoding.geocoding_service import GeocodingService
from src.presentation.bot.context import ConversationContext
from src.presentation.bot.error_handler import ErrorHandler
from src.presentation.bot.flow_engine import FlowEngine
from src.presentation.bot.handlers import legacy_check_handlers, legacy_report_handlers
from src.presentation.bot.message_parser import MessageParser
from src.presentation.bot.response_builder import ResponseBuilder
from src.presentation.bot.state_machine import ConversationStateMachine
from src.presentation.bot.states import ConversationState

if TYPE_CHECKING:
    from src.presentation.bot.flow_engine import FlowContext

logger = logging.getLogger(__name__)

# Type alias for router responses that can be text or interactive messages
type RouterResponse = dict[str, str | dict[str, Any]]

# Constants
DEFAULT_FLOW_PROMPT = "Please provide information"
FLOW_NOT_AVAILABLE = "Contact us feature is not available. Please try again later."


class MessageRouter:
    """Routes messages based on conversation state."""

    def __init__(
        self,
        state_machine: ConversationStateMachine,
        parser: MessageParser,
        response_builder: ResponseBuilder | None = None,
        check_if_stolen_handler: CheckIfStolenHandler | None = None,
        report_stolen_item_handler: ReportStolenItemHandler | None = None,
        error_handler: ErrorHandler | None = None,
        geocoding_service: GeocodingService | None = None,
        flow_engine: FlowEngine | None = None,
    ) -> None:
        """Initialize message router.

        Args:
            state_machine: Conversation state machine
            parser: Message parser for extracting data
            response_builder: Response builder for formatting messages
            check_if_stolen_handler: Handler for checking stolen items (optional)
            report_stolen_item_handler: Handler for reporting stolen items (optional)
            error_handler: Handler for mapping exceptions to user messages
            geocoding_service: Service for converting location text to coordinates (optional)
            flow_engine: Flow execution engine for configuration-driven flows (optional)
        """
        self.state_machine = state_machine
        self.parser = parser
        self.response_builder = response_builder or ResponseBuilder()
        self.check_if_stolen_handler = check_if_stolen_handler
        self.report_stolen_item_handler = report_stolen_item_handler
        self.error_handler = error_handler or ErrorHandler()
        self.geocoding_service = geocoding_service
        self.flow_engine = flow_engine

    async def route_message(
        self, phone_number: str, message_text: str
    ) -> dict[str, Any]:
        """Route message based on current conversation state.

        Args:
            phone_number: User's phone number
            message_text: Message text from user (or button_id/list_id)

        Returns:
            Response dictionary with reply (str or dict) and state (str)
        """
        # Get current context
        context = await self.state_machine.get_or_create(phone_number)

        # Handle global commands
        if message_text.lower().strip() in ["cancel", "quit", "exit", "stop"]:
            await self.state_machine.cancel(context)
            return {
                "reply": self.response_builder.format_cancel(),
                "state": ConversationState.CANCELLED.value,
            }

        # Route based on current state
        if context.state == ConversationState.IDLE:
            return await self._handle_idle(context)
        elif context.state == ConversationState.MAIN_MENU:
            return await self._handle_main_menu(context, message_text)
        elif context.state == ConversationState.ACTIVE_FLOW:
            return await self._handle_active_flow(context, message_text)
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
        elif context.state == ConversationState.REPORTING_DATE:
            return await self._handle_reporting_date(context, message_text)
        else:
            # Terminal state or unknown - reset to idle
            context = await self.state_machine.get_or_create(phone_number)
            return await self._handle_idle(context)

    async def _handle_idle(self, context: ConversationContext) -> RouterResponse:
        """Handle IDLE state - transition to main menu with interactive buttons."""
        new_context = await self.state_machine.transition(
            context, ConversationState.MAIN_MENU
        )
        return {
            "reply": self.response_builder.build_welcome_buttons(),
            "state": new_context.state.value,
        }

    async def _start_flow(
        self, context: ConversationContext, flow_id: str
    ) -> RouterResponse:
        """Start a configuration-driven flow.

        Args:
            context: Current conversation context
            flow_id: ID of the flow to start

        Returns:
            Router response with prompt and new state
        """
        flow_context = await self.flow_engine.start_flow(flow_id, context.phone_number)  # type: ignore[union-attr]
        new_context = await self.state_machine.transition(
            context, ConversationState.ACTIVE_FLOW
        )
        new_context = await self.state_machine.update_data(
            new_context,
            {"flow_id": flow_id, "flow_context": flow_context},
        )
        prompt = self.flow_engine.get_prompt(flow_context)  # type: ignore[union-attr]
        return {
            "reply": prompt or DEFAULT_FLOW_PROMPT,
            "state": new_context.state.value,
        }

    async def _handle_main_menu(
        self, context: ConversationContext, message_text: str
    ) -> RouterResponse:
        """Handle MAIN_MENU state - route to check or report flow.

        Supports both interactive button IDs and text input for backward compatibility.
        Uses flow engine if available, otherwise uses legacy state-based routing.
        """
        choice = message_text.strip()

        # Handle check item flow
        if choice in ["1", "check", "Check", "check_item"]:
            return await self._route_check_flow(context)

        # Handle report item flow
        if choice in ["2", "report", "Report", "report_item"]:
            return await self._route_report_flow(context)

        # Handle contact us flow
        if choice in ["3", "contact", "Contact", "contact_us"]:
            return await self._route_contact_flow(context)

        # Invalid choice
        return {
            "reply": self.response_builder.format_main_menu_invalid_choice(),
            "state": context.state.value,
        }

    async def _route_check_flow(self, context: ConversationContext) -> RouterResponse:
        """Route to check flow - use flow engine or legacy state."""
        if self.flow_engine is not None:
            return await self._start_flow(context, "check_item")

        # Legacy fallback
        new_context = await self.state_machine.transition(
            context, ConversationState.CHECKING_CATEGORY
        )
        return {
            "reply": self.response_builder.build_category_list(),
            "state": new_context.state.value,
        }

    async def _route_report_flow(self, context: ConversationContext) -> RouterResponse:
        """Route to report flow - use flow engine or legacy state."""
        if self.flow_engine is not None:
            return await self._start_flow(context, "report_item")

        # Legacy fallback
        new_context = await self.state_machine.transition(
            context, ConversationState.REPORTING_CATEGORY
        )
        return {
            "reply": self.response_builder.build_category_list(),
            "state": new_context.state.value,
        }

    async def _route_contact_flow(self, context: ConversationContext) -> RouterResponse:
        """Route to contact flow - config-only, no legacy fallback."""
        if self.flow_engine is not None:
            return await self._start_flow(context, "contact_us")

        # No legacy fallback for contact_us
        return {
            "reply": FLOW_NOT_AVAILABLE,
            "state": context.state.value,
        }

    async def _handle_active_flow(
        self, context: ConversationContext, message_text: str
    ) -> RouterResponse:
        """Handle ACTIVE_FLOW state - process input through flow engine."""
        if self.flow_engine is None:
            # Fall back to idle if no flow engine
            return await self._handle_idle(context)

        # Get flow context from conversation data
        flow_context = context.data.get("flow_context")
        if flow_context is None:
            # No active flow - reset to idle
            return await self._handle_idle(context)

        # Process input through flow engine
        new_flow_context = await self.flow_engine.process_input(
            cast("FlowContext", flow_context), message_text
        )

        # Check if flow is complete
        if new_flow_context.is_complete:
            # Flow completed - format results and transition to COMPLETE
            await self.state_machine.complete(context)
            result = new_flow_context.result or {}

            # Format result message
            if "matches" in result:
                reply = f"Search complete. Found {result['matches']} matching items."
            else:
                reply = "Flow completed successfully."

            return {
                "reply": reply,
                "state": ConversationState.COMPLETE.value,
            }
        else:
            # Flow still in progress - update context and get next prompt
            new_context = await self.state_machine.update_data(
                context,
                {"flow_context": new_flow_context},
            )
            prompt = self.flow_engine.get_prompt(new_flow_context)
            return {
                "reply": prompt or "Please continue",
                "state": new_context.state.value,
            }

    async def _handle_checking_category(
        self, context: ConversationContext, message_text: str
    ) -> dict[str, str]:
        """Handle CHECKING_CATEGORY state (legacy)."""
        return await legacy_check_handlers.handle_checking_category(
            context,
            message_text,
            self.state_machine,
            self.parser,
            self.response_builder,
        )

    async def _handle_checking_description(
        self, context: ConversationContext, message_text: str
    ) -> dict[str, str]:
        """Handle CHECKING_DESCRIPTION state (legacy)."""
        return await legacy_check_handlers.handle_checking_description(
            context,
            message_text,
            self.state_machine,
            self.parser,
            self.response_builder,
        )

    async def _handle_checking_location(
        self, context: ConversationContext, message_text: str
    ) -> dict[str, str]:
        """Handle CHECKING_LOCATION state (legacy)."""
        return await legacy_check_handlers.handle_checking_location(
            context,
            message_text,
            self.state_machine,
            self.parser,
            self.response_builder,
            self.error_handler,
            self.check_if_stolen_handler,
            self.geocoding_service,
        )

    async def _handle_reporting_category(
        self, context: ConversationContext, message_text: str
    ) -> dict[str, str]:
        """Handle REPORTING_CATEGORY state (legacy)."""
        return await legacy_report_handlers.handle_reporting_category(
            context,
            message_text,
            self.state_machine,
            self.parser,
            self.response_builder,
        )

    async def _handle_reporting_description(
        self, context: ConversationContext, message_text: str
    ) -> dict[str, str]:
        """Handle REPORTING_DESCRIPTION state (legacy)."""
        return await legacy_report_handlers.handle_reporting_description(
            context,
            message_text,
            self.state_machine,
            self.parser,
            self.response_builder,
        )

    async def _handle_reporting_location(
        self, context: ConversationContext, message_text: str
    ) -> dict[str, str]:
        """Handle REPORTING_LOCATION state (legacy)."""
        return await legacy_report_handlers.handle_reporting_location(
            context,
            message_text,
            self.state_machine,
            self.parser,
            self.response_builder,
        )

    async def _handle_reporting_date(
        self, context: ConversationContext, message_text: str
    ) -> dict[str, str]:
        """Handle REPORTING_DATE state (legacy)."""
        return await legacy_report_handlers.handle_reporting_date(
            context,
            message_text,
            self.state_machine,
            self.parser,
            self.response_builder,
            self.error_handler,
            self.report_stolen_item_handler,
            self.geocoding_service,
        )
