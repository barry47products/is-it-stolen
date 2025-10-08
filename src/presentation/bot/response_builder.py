"""Response builder for formatting bot messages."""

from typing import Any

from src.domain.constants import ButtonId
from src.domain.value_objects.item_category import ItemCategory
from src.infrastructure.whatsapp.constants import (
    INTERACTIVE_TYPE_BUTTON,
    INTERACTIVE_TYPE_LIST,
    MAX_BUTTON_TITLE_LENGTH,
    MAX_BUTTONS_PER_MESSAGE,
    MAX_ROWS_PER_LIST,
    MAX_SECTIONS_PER_LIST,
    MESSAGE_TYPE_INTERACTIVE,
    MIN_BUTTONS_REQUIRED,
    MIN_SECTIONS_REQUIRED,
    REPLY_TYPE,
)
from src.presentation.bot.messages import (
    CANCELLATION_MESSAGES,
    CHECK_FLOW_MESSAGES,
    ERROR_MESSAGES,
    LABEL_CHECK_ITEM,
    LABEL_REPORT_ITEM,
    LABEL_SELECT_CATEGORY,
    REPORT_FLOW_MESSAGES,
    WELCOME_MESSAGES,
)


class ResponseBuilder:
    """Builds formatted responses for WhatsApp bot."""

    def format_welcome(self) -> str:
        """Format welcome message with main menu.

        Returns:
            Formatted welcome message
        """
        return WELCOME_MESSAGES.welcome

    def format_cancel(self) -> str:
        """Format cancellation message.

        Returns:
            Formatted cancel message
        """
        return CANCELLATION_MESSAGES.conversation_cancelled

    def format_checking_category_prompt(self) -> str:
        """Format prompt for checking category input.

        Returns:
            Formatted category prompt
        """
        return CHECK_FLOW_MESSAGES.category_prompt

    def format_category_confirmation(self, category: ItemCategory) -> str:
        """Format category confirmation message.

        Args:
            category: Confirmed item category

        Returns:
            Formatted confirmation message
        """
        return CHECK_FLOW_MESSAGES.category_confirmation(category)

    def format_invalid_category(self) -> str:
        """Format invalid category error message.

        Returns:
            Formatted error message
        """
        return ERROR_MESSAGES.invalid_category

    def format_location_prompt(self) -> str:
        """Format generic location prompt.

        Returns:
            Formatted location prompt
        """
        return CHECK_FLOW_MESSAGES.location_prompt

    def format_checking_location_prompt(self) -> str:
        """Format location prompt for checking flow.

        Returns:
            Formatted location prompt with skip option
        """
        return CHECK_FLOW_MESSAGES.location_prompt

    def format_reporting_location_prompt(self) -> str:
        """Format location prompt for reporting flow.

        Returns:
            Formatted location prompt with unknown option
        """
        return REPORT_FLOW_MESSAGES.location_prompt

    def format_checking_complete(
        self, matches_found: bool, match_count: int = 0
    ) -> str:
        """Format checking flow completion message.

        Args:
            matches_found: Whether matches were found
            match_count: Number of matches found

        Returns:
            Formatted completion message
        """
        if matches_found:
            return CHECK_FLOW_MESSAGES.search_complete_with_matches(match_count)
        else:
            return CHECK_FLOW_MESSAGES.search_complete_no_matches

    def format_reporting_category_prompt(self) -> str:
        """Format prompt for reporting category.

        Returns:
            Formatted reporting category prompt
        """
        return REPORT_FLOW_MESSAGES.category_prompt

    def format_reporting_confirmation(self, category: ItemCategory) -> str:
        """Format reporting category confirmation.

        Args:
            category: Confirmed item category

        Returns:
            Formatted confirmation message
        """
        return REPORT_FLOW_MESSAGES.category_confirmation(category)

    def format_reporting_complete(self) -> str:
        """Format reporting flow completion message.

        Returns:
            Formatted completion message
        """
        return REPORT_FLOW_MESSAGES.report_complete

    def format_main_menu_invalid_choice(self) -> str:
        """Format invalid main menu choice message.

        Returns:
            Formatted error message
        """
        return WELCOME_MESSAGES.main_menu_invalid_choice

    def build_reply_buttons(
        self, body: str, buttons: list[dict[str, str]]
    ) -> dict[str, Any]:
        """Build reply buttons interactive message payload.

        Args:
            body: Message body text
            buttons: List of button dicts with 'id' and 'title' keys (max 3)

        Returns:
            Dict with Meta WhatsApp Cloud API interactive message payload

        Raises:
            ValueError: If buttons list is invalid (empty, >3 buttons, title too long)
        """
        if len(buttons) < MIN_BUTTONS_REQUIRED:
            raise ValueError(f"At least {MIN_BUTTONS_REQUIRED} button required")
        if len(buttons) > MAX_BUTTONS_PER_MESSAGE:
            raise ValueError(f"Maximum {MAX_BUTTONS_PER_MESSAGE} buttons allowed")

        # Validate button title lengths
        for button in buttons:
            if len(button["title"]) > MAX_BUTTON_TITLE_LENGTH:
                raise ValueError(
                    f"Button title '{button['title']}' cannot exceed "
                    f"{MAX_BUTTON_TITLE_LENGTH} characters"
                )

        action_buttons = [
            {
                "type": REPLY_TYPE,
                "reply": {"id": btn["id"], "title": btn["title"]},
            }
            for btn in buttons
        ]

        return {
            "type": MESSAGE_TYPE_INTERACTIVE,
            "interactive": {
                "type": INTERACTIVE_TYPE_BUTTON,
                "body": {"text": body},
                "action": {"buttons": action_buttons},
            },
        }

    def build_list_message(
        self,
        body: str,
        button_text: str,
        sections: list[dict[str, Any]],
        header: str | None = None,
    ) -> dict[str, Any]:
        """Build list message interactive message payload.

        Args:
            body: Message body text
            button_text: Text for list button
            sections: List of section dicts with 'title' and 'rows' keys
            header: Optional header text

        Returns:
            Dict with Meta WhatsApp Cloud API interactive message payload

        Raises:
            ValueError: If sections is invalid (empty, >10 sections, >10 total rows)
        """
        if len(sections) < MIN_SECTIONS_REQUIRED:
            raise ValueError(f"At least {MIN_SECTIONS_REQUIRED} section required")
        if len(sections) > MAX_SECTIONS_PER_LIST:
            raise ValueError(f"Maximum {MAX_SECTIONS_PER_LIST} sections allowed")

        total_rows = sum(len(section.get("rows", [])) for section in sections)
        if total_rows > MAX_ROWS_PER_LIST:
            raise ValueError(
                f"Maximum {MAX_ROWS_PER_LIST} rows allowed across all sections"
            )

        interactive: dict[str, Any] = {
            "type": INTERACTIVE_TYPE_LIST,
            "body": {"text": body},
            "action": {"button": button_text, "sections": sections},
        }

        if header:
            interactive["header"] = {"type": "text", "text": header}

        return {"type": MESSAGE_TYPE_INTERACTIVE, "interactive": interactive}

    def build_category_list(self) -> dict[str, Any]:
        """Build category selection list message.

        Returns:
            Dict with Meta WhatsApp Cloud API interactive list message
        """
        sections = [
            {
                "title": "Common Items",
                "rows": [
                    {
                        "id": "bicycle",
                        "title": "Bicycle",
                        "description": "Bikes, e-bikes, scooters",
                    },
                    {
                        "id": "phone",
                        "title": "Phone",
                        "description": "Mobile phones, smartphones",
                    },
                    {
                        "id": "laptop",
                        "title": "Laptop",
                        "description": "Laptops, tablets, computers",
                    },
                    {"id": "car", "title": "Car", "description": "Cars, vehicles"},
                ],
            }
        ]

        return self.build_list_message(
            body="What type of item?",
            button_text=LABEL_SELECT_CATEGORY,
            sections=sections,
        )

    def build_welcome_buttons(self) -> dict[str, Any]:
        """Build welcome/main menu buttons.

        Returns:
            Dict with Meta WhatsApp Cloud API interactive button message
        """
        buttons = [
            {"id": ButtonId.CHECK_ITEM.value, "title": LABEL_CHECK_ITEM},
            {"id": ButtonId.REPORT_ITEM.value, "title": LABEL_REPORT_ITEM},
        ]

        return self.build_reply_buttons(
            body=WELCOME_MESSAGES.welcome_buttons_body,
            buttons=buttons,
        )
