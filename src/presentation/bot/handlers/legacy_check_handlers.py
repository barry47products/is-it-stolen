"""Legacy handlers for check item flow (CHECKING_* states).

DEPRECATED: These handlers support the old state-based check flow.
In the future, all check flows will use the config-driven ACTIVE_FLOW pattern.
See Issue #114 for migration plan.
"""

import logging

from src.application.queries.check_if_stolen import CheckIfStolenHandler
from src.infrastructure.geocoding.geocoding_service import GeocodingService
from src.infrastructure.metrics.metrics_service import get_metrics_service
from src.presentation.bot.context import ConversationContext
from src.presentation.bot.error_handler import ErrorHandler
from src.presentation.bot.handlers.handler_utils import build_check_query
from src.presentation.bot.message_parser import MessageParser
from src.presentation.bot.response_builder import ResponseBuilder
from src.presentation.bot.state_machine import ConversationStateMachine
from src.presentation.bot.states import ConversationState
from src.presentation.utils.redaction import redact_phone_number

logger = logging.getLogger(__name__)

# Type alias for handler responses
type HandlerResponse = dict[str, str]


async def handle_checking_category(
    context: ConversationContext,
    message_text: str,
    state_machine: ConversationStateMachine,
    parser: MessageParser,
    response_builder: ResponseBuilder,
) -> HandlerResponse:
    """Handle CHECKING_CATEGORY state."""
    category = parser.parse_category(message_text)

    if category:
        # Store category and move to description
        new_context = await state_machine.update_data(
            context, {"category": category.value}
        )
        new_context = await state_machine.transition(
            new_context, ConversationState.CHECKING_DESCRIPTION
        )
        return {
            "reply": response_builder.format_category_confirmation(category),
            "state": new_context.state.value,
        }
    else:
        return {
            "reply": response_builder.format_invalid_category(),
            "state": context.state.value,
        }


async def handle_checking_description(
    context: ConversationContext,
    message_text: str,
    state_machine: ConversationStateMachine,
    parser: MessageParser,
    response_builder: ResponseBuilder,
) -> HandlerResponse:
    """Handle CHECKING_DESCRIPTION state."""
    # Extract brand/model
    brand_model = parser.extract_brand_model(message_text)

    # Store description and move to location
    new_context = await state_machine.update_data(
        context, {"description": message_text, "brand_model": brand_model}
    )
    new_context = await state_machine.transition(
        new_context, ConversationState.CHECKING_LOCATION
    )

    return {
        "reply": response_builder.format_checking_location_prompt(),
        "state": new_context.state.value,
    }


async def handle_checking_location(
    context: ConversationContext,
    message_text: str,
    state_machine: ConversationStateMachine,
    parser: MessageParser,
    response_builder: ResponseBuilder,
    error_handler: ErrorHandler,
    check_if_stolen_handler: CheckIfStolenHandler | None = None,
    geocoding_service: GeocodingService | None = None,
) -> HandlerResponse:
    """Handle CHECKING_LOCATION state."""
    if message_text.lower().strip() == "skip":
        location = None
    else:
        location = parser.parse_location_text(message_text)

    # Store location and complete
    new_context = await state_machine.update_data(context, {"location": location})
    await state_machine.complete(new_context)

    # Query database for stolen items if handler is available
    if check_if_stolen_handler is not None:
        try:
            # Build query from collected data
            query = await build_check_query(new_context, geocoding_service)

            # Execute query
            result = await check_if_stolen_handler.handle(query)

            # Track metrics
            metrics = get_metrics_service()
            metrics.increment_items_checked()

            # Format response based on results
            matches_found = len(result.matches) > 0
            match_count = len(result.matches)

            return {
                "reply": response_builder.format_checking_complete(
                    matches_found=matches_found, match_count=match_count
                ),
                "state": ConversationState.COMPLETE.value,
            }
        except Exception as error:
            # Log and return user-friendly error message
            logger.error(
                f"Error checking stolen items: {error}",
                exc_info=True,
                extra={"phone_number": redact_phone_number(new_context.phone_number)},
            )
            return {
                "reply": error_handler.handle_error(error),
                "state": ConversationState.COMPLETE.value,
            }
    else:
        # No handler available - return placeholder response
        return {
            "reply": response_builder.format_checking_complete(matches_found=False),
            "state": ConversationState.COMPLETE.value,
        }
