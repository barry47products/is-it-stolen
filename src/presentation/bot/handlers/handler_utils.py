"""Utility functions for building queries and commands from conversation context."""

import logging
from datetime import UTC, datetime
from typing import Any

from src.application.commands.report_stolen_item import ReportStolenItemCommand
from src.application.queries.check_if_stolen import CheckIfStolenQuery
from src.infrastructure.geocoding.geocoding_service import GeocodingService
from src.presentation.bot.context import ConversationContext

logger = logging.getLogger(__name__)


async def build_check_query(
    context: ConversationContext, geocoding_service: GeocodingService | None = None
) -> CheckIfStolenQuery:
    """Build CheckIfStolenQuery from conversation context data.

    Args:
        context: Conversation context with collected data
        geocoding_service: Optional geocoding service for location text

    Returns:
        CheckIfStolenQuery ready to execute
    """
    data = context.data
    description = str(data.get("description", ""))
    brand_model_value = data.get("brand_model", "")
    brand_model = str(brand_model_value) if brand_model_value else None
    category = data.get("category")
    location_text = data.get("location")

    # Geocode location if provided
    latitude = None
    longitude = None
    if location_text and geocoding_service:
        result = await geocode_location(str(location_text), geocoding_service)
        if result:
            latitude = result.latitude
            longitude = result.longitude

    return CheckIfStolenQuery(
        description=description,
        brand=brand_model,
        category=str(category) if category else None,
        latitude=latitude,
        longitude=longitude,
    )


async def build_report_command(
    context: ConversationContext, geocoding_service: GeocodingService | None = None
) -> ReportStolenItemCommand:
    """Build ReportStolenItemCommand from conversation context data.

    Args:
        context: Conversation context with collected data
        geocoding_service: Optional geocoding service for location text

    Returns:
        ReportStolenItemCommand ready to execute
    """
    data = context.data
    description = str(data.get("description", ""))
    brand_model_value = data.get("brand_model", "")
    brand_model = str(brand_model_value) if brand_model_value else None
    category = data.get("category", "unknown")
    location_text = data.get("location")

    # Geocode location if provided, otherwise use default coordinates
    latitude = 0.0
    longitude = 0.0
    if location_text and geocoding_service:
        result = await geocode_location(str(location_text), geocoding_service)
        if result:
            latitude = result.latitude
            longitude = result.longitude

    # Get stolen date from context, or default to now if not provided
    stolen_date_raw = data.get("stolen_date")
    if isinstance(stolen_date_raw, datetime):
        stolen_date = stolen_date_raw
    elif isinstance(stolen_date_raw, str):
        # Parse ISO format string back to datetime
        stolen_date = datetime.fromisoformat(stolen_date_raw)
    else:
        # No date provided, use current time
        stolen_date = datetime.now(UTC)

    return ReportStolenItemCommand(
        reporter_phone=context.phone_number,
        item_type=str(category),
        description=description,
        stolen_date=stolen_date,
        latitude=latitude,
        longitude=longitude,
        brand=brand_model,
    )


async def geocode_location(
    location_text: str, geocoding_service: GeocodingService
) -> Any:
    """Geocode location text to coordinates.

    Args:
        location_text: Location as text
        geocoding_service: Geocoding service instance

    Returns:
        GeocodingResult if successful, None otherwise
    """
    try:
        return await geocoding_service.geocode(location_text)
    except Exception as error:
        logger.warning(f"Geocoding failed for '{location_text}': {error}")
        return None
