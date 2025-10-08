"""Legacy handlers for report item flow (REPORTING_* states).

DEPRECATED: These handlers support the old state-based report flow.
In the future, all report flows will use the config-driven ACTIVE_FLOW pattern.
See Issue #114 for migration plan.
"""

import logging

from src.application.commands.report_stolen_item import ReportStolenItemHandler
from src.infrastructure.geocoding.geocoding_service import GeocodingService
from src.infrastructure.metrics.metrics_service import get_metrics_service
from src.presentation.bot.context import ConversationContext
from src.presentation.bot.error_handler import ErrorHandler
from src.presentation.bot.handlers.handler_utils import build_report_command
from src.presentation.bot.message_parser import MessageParser
from src.presentation.bot.response_builder import ResponseBuilder
from src.presentation.bot.state_machine import ConversationStateMachine
from src.presentation.bot.states import ConversationState
from src.presentation.utils.redaction import redact_phone_number

logger = logging.getLogger(__name__)

# Type alias for handler responses
type HandlerResponse = dict[str, str]


async def handle_reporting_category(
    context: ConversationContext,
    message_text: str,
    state_machine: ConversationStateMachine,
    parser: MessageParser,
    response_builder: ResponseBuilder,
) -> HandlerResponse:
    """Handle REPORTING_CATEGORY state."""
    category = parser.parse_category(message_text)

    if category:
        new_context = await state_machine.update_data(
            context, {"category": category.value}
        )
        new_context = await state_machine.transition(
            new_context, ConversationState.REPORTING_DESCRIPTION
        )
        return {
            "reply": response_builder.format_reporting_confirmation(category),
            "state": new_context.state.value,
        }
    else:
        return {
            "reply": response_builder.format_invalid_category(),
            "state": context.state.value,
        }


async def handle_reporting_description(
    context: ConversationContext,
    message_text: str,
    state_machine: ConversationStateMachine,
    parser: MessageParser,
    response_builder: ResponseBuilder,
) -> HandlerResponse:
    """Handle REPORTING_DESCRIPTION state."""
    brand_model = parser.extract_brand_model(message_text)

    new_context = await state_machine.update_data(
        context, {"description": message_text, "brand_model": brand_model}
    )
    new_context = await state_machine.transition(
        new_context, ConversationState.REPORTING_LOCATION
    )

    return {
        "reply": response_builder.format_reporting_location_prompt(),
        "state": new_context.state.value,
    }


async def handle_reporting_location(
    context: ConversationContext,
    message_text: str,
    state_machine: ConversationStateMachine,
    parser: MessageParser,
    response_builder: ResponseBuilder,
) -> HandlerResponse:
    """Handle REPORTING_LOCATION state."""
    if message_text.lower().strip() == "unknown":
        location = None
    else:
        location = parser.parse_location_text(message_text)

    new_context = await state_machine.update_data(context, {"location": location})
    await state_machine.transition(new_context, ConversationState.REPORTING_DATE)

    return {
        "reply": response_builder.format_reporting_date_prompt(),
        "state": ConversationState.REPORTING_DATE.value,
    }


async def handle_reporting_date(
    context: ConversationContext,
    message_text: str,
    state_machine: ConversationStateMachine,
    parser: MessageParser,
    response_builder: ResponseBuilder,
    error_handler: ErrorHandler,
    report_stolen_item_handler: ReportStolenItemHandler | None = None,
    geocoding_service: GeocodingService | None = None,
) -> HandlerResponse:
    """Handle REPORTING_DATE state."""
    # Parse the date
    parsed_date = parser.parse_date(message_text)

    if parsed_date is None:
        # Invalid date - stay in same state and ask again
        return {
            "reply": response_builder.format_invalid_date(),
            "state": ConversationState.REPORTING_DATE.value,
        }

    # Store date and complete reporting flow
    new_context = await state_machine.update_data(context, {"stolen_date": parsed_date})
    await state_machine.complete(new_context)

    # Save stolen item report if handler is available
    if report_stolen_item_handler is not None:
        try:
            # Build command from collected data
            command = await build_report_command(new_context, geocoding_service)

            # Execute command
            item_id = await report_stolen_item_handler.handle(command)

            # Track metrics
            metrics = get_metrics_service()
            metrics.increment_reports_created()

            # Log success
            logger.info(
                "Stolen item reported successfully",
                extra={
                    "item_id": str(item_id),
                    "phone_number": redact_phone_number(new_context.phone_number),
                },
            )

            return {
                "reply": response_builder.format_reporting_complete(),
                "state": ConversationState.COMPLETE.value,
            }
        except Exception as error:
            # Log and return user-friendly error message
            logger.error(
                f"Error reporting stolen item: {error}",
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
            "reply": response_builder.format_reporting_complete(),
            "state": ConversationState.COMPLETE.value,
        }
