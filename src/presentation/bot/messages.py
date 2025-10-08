"""User-facing message templates and constants.

This module contains all user-facing strings, messages, and prompts used in
the WhatsApp bot. Centralizing messages here makes it easier to maintain
consistency and prepare for future internationalization (i18n).
"""

from dataclasses import dataclass

from src.domain.value_objects.item_category import ItemCategory

# Emojis
EMOJI_WAVE = "👋"
EMOJI_CHECKMARK = "✅"
EMOJI_CROSS = "❌"
EMOJI_MAGNIFYING_GLASS = "🔍"
EMOJI_PIN = "📍"
EMOJI_NOTEPAD = "📝"
EMOJI_WARNING = "⚠️"
EMOJI_HOURGLASS = "⏳"
EMOJI_ONE = "1️⃣"
EMOJI_TWO = "2️⃣"
EMOJI_THREE = "3️⃣"

# Action Labels
LABEL_CHECK_ITEM = "Check Item"
LABEL_REPORT_ITEM = "Report Item"
LABEL_CONTACT_US = "Contact us"
LABEL_SELECT_CATEGORY = "Select Category"

# Command Instructions
TEXT_CANCEL_INSTRUCTION = "Type 'cancel' to exit."
TEXT_CANCEL_TO_GO_BACK = "Type 'cancel' to go back."

# Item Category Examples
TEXT_CATEGORY_EXAMPLES = "Examples: bike, phone, laptop, car"
TEXT_CATEGORY_OPTIONS = "Please try again with: bike, phone, laptop, or car"

# Location Instructions
TEXT_LOCATION_TYPE = "• Type a location (e.g., 'Main Street, downtown')"
TEXT_LOCATION_SEND = "• Send your current location"
TEXT_LOCATION_SKIP = "• Type 'skip' if you don't know"
TEXT_LOCATION_UNKNOWN = "• Type 'unknown' if you're not sure"


@dataclass(frozen=True)
class WelcomeMessages:
    """Welcome and main menu messages."""

    welcome: str = (
        f"{EMOJI_WAVE} Welcome to Is It Stolen!\n\n"
        "What would you like to do?\n"
        f"{EMOJI_ONE} Check if an item is stolen\n"
        f"{EMOJI_TWO} Report a stolen item\n"
        f"{EMOJI_THREE} Contact us\n\n"
        "Reply with 1, 2, or 3, or type 'cancel' to exit."
    )

    welcome_buttons_body: str = (
        f"{EMOJI_WAVE} Welcome to Is It Stolen!\n\nWhat would you like to do?"
    )

    main_menu_invalid_choice: str = (
        "Please choose an option:\n"
        f"{EMOJI_ONE} Check if an item is stolen\n"
        f"{EMOJI_TWO} Report a stolen item\n\n"
        f"{TEXT_CANCEL_INSTRUCTION}"
    )


@dataclass(frozen=True)
class CancellationMessages:
    """Cancellation and exit messages."""

    conversation_cancelled: str = (
        "Conversation cancelled. Send any message to start again."
    )


@dataclass(frozen=True)
class CheckFlowMessages:
    """Messages for the check item flow."""

    category_prompt: str = (
        f"{EMOJI_MAGNIFYING_GLASS} Check if stolen\n\n"
        "What type of item do you want to check?\n"
        f"{TEXT_CATEGORY_EXAMPLES}\n\n"
        f"{TEXT_CANCEL_TO_GO_BACK}"
    )

    location_prompt: str = (
        f"{EMOJI_PIN} Where was it last seen or stolen?\n\n"
        "You can either:\n"
        f"{TEXT_LOCATION_TYPE}\n"
        f"{TEXT_LOCATION_SEND}\n"
        f"{TEXT_LOCATION_SKIP}"
    )

    @staticmethod
    def category_confirmation(category: ItemCategory) -> str:
        """Format category confirmation message.

        Args:
            category: Confirmed item category

        Returns:
            Formatted confirmation message
        """
        return (
            f"{EMOJI_CHECKMARK} Got it, checking for: {category.value}\n\n"
            "Please describe the item (brand, model, color, etc.):\n"
            "Example: Red Trek mountain bike, serial ABC123"
        )

    @staticmethod
    def search_complete_with_matches(match_count: int) -> str:
        """Format search complete message with matches.

        Args:
            match_count: Number of matches found

        Returns:
            Formatted completion message
        """
        plural = "es" if match_count != 1 else ""
        return (
            f"{EMOJI_MAGNIFYING_GLASS} Search complete!\n\n"
            f"Found {match_count} potential match{plural}.\n"
            "We'll send details in the next message.\n\n"
            "Send any message to start a new search."
        )

    search_complete_no_matches: str = (
        f"{EMOJI_MAGNIFYING_GLASS} Searching for matches...\n\n"
        "No stolen items found matching your description.\n\n"
        "Send any message to start a new search."
    )


@dataclass(frozen=True)
class ReportFlowMessages:
    """Messages for the report item flow."""

    category_prompt: str = (
        f"{EMOJI_NOTEPAD} Report stolen item\n\n"
        "What type of item was stolen?\n"
        f"{TEXT_CATEGORY_EXAMPLES}\n\n"
        f"{TEXT_CANCEL_TO_GO_BACK}"
    )

    location_prompt: str = (
        f"{EMOJI_PIN} Where was it stolen?\n\n"
        "You can either:\n"
        "• Type the location\n"
        f"{TEXT_LOCATION_SEND}\n"
        f"{TEXT_LOCATION_UNKNOWN}"
    )

    report_complete: str = (
        f"{EMOJI_CHECKMARK} Thank you for reporting!\n\n"
        "Your stolen item has been recorded.\n"
        "We'll notify you if there are any matches.\n\n"
        "Send any message to make another report."
    )

    @staticmethod
    def category_confirmation(category: ItemCategory) -> str:
        """Format reporting category confirmation.

        Args:
            category: Confirmed item category

        Returns:
            Formatted confirmation message
        """
        return (
            f"{EMOJI_CHECKMARK} Reporting stolen: {category.value}\n\n"
            "Please describe the item in detail:\n"
            "Include: brand, model, color, serial number, any unique features"
        )


@dataclass(frozen=True)
class ErrorMessages:
    """Error messages for various failure scenarios."""

    invalid_category: str = (
        f"{EMOJI_CROSS} I didn't recognize that item type.\n\n{TEXT_CATEGORY_OPTIONS}"
    )

    invalid_location: str = (
        f"{EMOJI_CROSS} The location you provided is invalid.\n\n"
        "Please provide a valid location or type 'skip' to continue without location."
    )

    item_not_found: str = (
        f"{EMOJI_CROSS} The item you're looking for doesn't exist.\n\n"
        "It may have been deleted or the ID is incorrect."
    )

    rate_limit_exceeded: str = (
        f"{EMOJI_HOURGLASS} You're sending messages too quickly.\n\n"
        "Please wait a moment and try again."
    )

    @staticmethod
    def rate_limit_with_time(retry_minutes: int, retry_seconds: int) -> str:
        """Format rate limit message with specific wait time.

        Args:
            retry_minutes: Minutes to wait
            retry_seconds: Seconds to wait

        Returns:
            Formatted rate limit message
        """
        if retry_minutes > 0:
            retry_msg = f"{retry_minutes} minute{'s' if retry_minutes != 1 else ''}"
            if retry_seconds > 0:
                retry_msg += (
                    f" and {retry_seconds} second{'s' if retry_seconds != 1 else ''}"
                )
        else:
            retry_msg = f"{retry_seconds} second{'s' if retry_seconds != 1 else ''}"

        return (
            f"{EMOJI_HOURGLASS} You're sending messages too quickly.\n\n"
            f"Please wait {retry_msg} before trying again.\n"
            "This helps us keep the service running smoothly for everyone."
        )

    repository_error: str = (
        f"{EMOJI_WARNING} We're experiencing a temporary problem.\n\n"
        "Please try again in a few moments.\n"
        "If the problem persists, please contact support."
    )

    whatsapp_api_error: str = (
        f"{EMOJI_WARNING} We're having trouble sending your message.\n\n"
        "Please try again in a moment."
    )

    whatsapp_error: str = f"{EMOJI_WARNING} There was a problem with WhatsApp.\n\nPlease try again shortly."

    invalid_state_transition: str = (
        f"{EMOJI_WARNING} Something went wrong with the conversation flow.\n\n"
        "Let's start over. Send any message to begin again."
    )

    conversation_error: str = (
        f"{EMOJI_WARNING} There was a problem with the conversation.\n\n"
        "Please try sending your message again, or type 'cancel' to start over."
    )

    domain_error: str = (
        f"{EMOJI_CROSS} There was a problem processing your request.\n\n"
        "Please try again or type 'cancel' to start over."
    )

    unexpected_error: str = (
        f"{EMOJI_CROSS} Something unexpected went wrong.\n\n"
        "Please try again. If the problem persists, contact support."
    )


# Global message instances (singleton pattern)
WELCOME_MESSAGES = WelcomeMessages()
CANCELLATION_MESSAGES = CancellationMessages()
CHECK_FLOW_MESSAGES = CheckFlowMessages()
REPORT_FLOW_MESSAGES = ReportFlowMessages()
ERROR_MESSAGES = ErrorMessages()
