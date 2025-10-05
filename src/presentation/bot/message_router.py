"""Message router for handling state-based message routing."""

import logging
from datetime import UTC, datetime

from src.application.commands.report_stolen_item import (
    ReportStolenItemCommand,
    ReportStolenItemHandler,
)
from src.application.queries.check_if_stolen import (
    CheckIfStolenHandler,
    CheckIfStolenQuery,
)
from src.presentation.bot.context import ConversationContext
from src.presentation.bot.error_handler import ErrorHandler
from src.presentation.bot.message_parser import MessageParser
from src.presentation.bot.response_builder import ResponseBuilder
from src.presentation.bot.state_machine import ConversationStateMachine
from src.presentation.bot.states import ConversationState

logger = logging.getLogger(__name__)


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
    ) -> None:
        """Initialize message router.

        Args:
            state_machine: Conversation state machine
            parser: Message parser for extracting data
            response_builder: Response builder for formatting messages
            check_if_stolen_handler: Handler for checking stolen items (optional)
            report_stolen_item_handler: Handler for reporting stolen items (optional)
            error_handler: Handler for mapping exceptions to user messages
        """
        self.state_machine = state_machine
        self.parser = parser
        self.response_builder = response_builder or ResponseBuilder()
        self.check_if_stolen_handler = check_if_stolen_handler
        self.report_stolen_item_handler = report_stolen_item_handler
        self.error_handler = error_handler or ErrorHandler()

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
                "reply": self.response_builder.format_cancel(),
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
            "reply": self.response_builder.format_welcome(),
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
                "reply": self.response_builder.format_checking_category_prompt(),
                "state": new_context.state.value,
            }
        elif choice in ["2", "report", "Report"]:
            new_context = await self.state_machine.transition(
                context, ConversationState.REPORTING_CATEGORY
            )
            return {
                "reply": self.response_builder.format_reporting_category_prompt(),
                "state": new_context.state.value,
            }
        else:
            return {
                "reply": self.response_builder.format_main_menu_invalid_choice(),
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
                "reply": self.response_builder.format_category_confirmation(category),
                "state": new_context.state.value,
            }
        else:
            return {
                "reply": self.response_builder.format_invalid_category(),
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
            "reply": self.response_builder.format_checking_location_prompt(),
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

        # Query database for stolen items if handler is available
        if self.check_if_stolen_handler is not None:
            try:
                # Build query from collected data
                query = self._build_check_query(new_context)

                # Execute query
                result = await self.check_if_stolen_handler.handle(query)

                # Format response based on results
                matches_found = len(result.matches) > 0
                match_count = len(result.matches)

                return {
                    "reply": self.response_builder.format_checking_complete(
                        matches_found=matches_found, match_count=match_count
                    ),
                    "state": ConversationState.COMPLETE.value,
                }
            except Exception as error:
                # Log and return user-friendly error message
                logger.error(
                    f"Error checking stolen items: {error}",
                    exc_info=True,
                    extra={"phone_number": new_context.phone_number},
                )
                return {
                    "reply": self.error_handler.handle_error(error),
                    "state": ConversationState.COMPLETE.value,
                }
        else:
            # No handler available - return placeholder response
            return {
                "reply": self.response_builder.format_checking_complete(
                    matches_found=False
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
                "reply": self.response_builder.format_reporting_confirmation(category),
                "state": new_context.state.value,
            }
        else:
            return {
                "reply": self.response_builder.format_invalid_category(),
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
            "reply": self.response_builder.format_reporting_location_prompt(),
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

        # Save stolen item report if handler is available
        if self.report_stolen_item_handler is not None:
            try:
                # Build command from collected data
                command = self._build_report_command(new_context)

                # Execute command
                item_id = await self.report_stolen_item_handler.handle(command)

                # Log success
                logger.info(
                    "Stolen item reported successfully",
                    extra={
                        "item_id": str(item_id),
                        "phone_number": new_context.phone_number,
                    },
                )

                return {
                    "reply": self.response_builder.format_reporting_complete(),
                    "state": ConversationState.COMPLETE.value,
                }
            except Exception as error:
                # Log and return user-friendly error message
                logger.error(
                    f"Error reporting stolen item: {error}",
                    exc_info=True,
                    extra={"phone_number": new_context.phone_number},
                )
                return {
                    "reply": self.error_handler.handle_error(error),
                    "state": ConversationState.COMPLETE.value,
                }
        else:
            # No handler available - return placeholder response
            return {
                "reply": self.response_builder.format_reporting_complete(),
                "state": ConversationState.COMPLETE.value,
            }

    def _build_check_query(self, context: ConversationContext) -> CheckIfStolenQuery:
        """Build CheckIfStolenQuery from conversation context data.

        Args:
            context: Conversation context with collected data

        Returns:
            CheckIfStolenQuery ready to execute
        """
        data = context.data
        description = str(data.get("description", ""))
        brand_model_value = data.get("brand_model", "")
        brand_model = str(brand_model_value) if brand_model_value else None
        category = data.get("category")
        location_text = data.get("location")

        # Parse location if provided
        latitude = None
        longitude = None
        if location_text:
            # TODO(#37): Parse actual coordinates from location text using geocoding
            # For now, location is just text - will need geocoding service
            pass

        return CheckIfStolenQuery(
            description=description,
            brand=brand_model,
            category=str(category) if category else None,
            latitude=latitude,
            longitude=longitude,
        )

    def _build_report_command(
        self, context: ConversationContext
    ) -> ReportStolenItemCommand:
        """Build ReportStolenItemCommand from conversation context data.

        Args:
            context: Conversation context with collected data

        Returns:
            ReportStolenItemCommand ready to execute
        """
        data = context.data
        description = str(data.get("description", ""))
        brand_model_value = data.get("brand_model", "")
        brand_model = str(brand_model_value) if brand_model_value else None
        category = data.get("category", "unknown")
        location_text = data.get("location")

        # Parse location if provided (use placeholder coordinates for now)
        # TODO(#37): Implement geocoding to convert location text to coordinates
        latitude = 0.0
        longitude = 0.0
        if location_text:
            # Placeholder - will need actual geocoding service
            pass

        return ReportStolenItemCommand(
            reporter_phone=context.phone_number,
            item_type=str(category),
            description=description,
            stolen_date=datetime.now(UTC),  # Use current time as placeholder
            latitude=latitude,
            longitude=longitude,
            brand=brand_model,
        )
