"""Response builder for formatting bot messages."""

from typing import Any

from src.domain.value_objects.item_category import ItemCategory


class ResponseBuilder:
    """Builds formatted responses for WhatsApp bot."""

    def format_welcome(self) -> str:
        """Format welcome message with main menu.

        Returns:
            Formatted welcome message
        """
        return (
            "👋 Welcome to Is It Stolen!\n\n"
            "What would you like to do?\n"
            "1️⃣ Check if an item is stolen\n"
            "2️⃣ Report a stolen item\n"
            "3️⃣ Contact us\n\n"
            "Reply with 1, 2, or 3, or type 'cancel' to exit."
        )

    def format_cancel(self) -> str:
        """Format cancellation message.

        Returns:
            Formatted cancel message
        """
        return "Conversation cancelled. Send any message to start again."

    def format_checking_category_prompt(self) -> str:
        """Format prompt for checking category input.

        Returns:
            Formatted category prompt
        """
        return (
            "🔍 Check if stolen\n\n"
            "What type of item do you want to check?\n"
            "Examples: bike, phone, laptop, car\n\n"
            "Type 'cancel' to go back."
        )

    def format_category_confirmation(self, category: ItemCategory) -> str:
        """Format category confirmation message.

        Args:
            category: Confirmed item category

        Returns:
            Formatted confirmation message
        """
        return (
            f"✅ Got it, checking for: {category.value}\n\n"
            "Please describe the item (brand, model, color, etc.):\n"
            "Example: Red Trek mountain bike, serial ABC123"
        )

    def format_invalid_category(self) -> str:
        """Format invalid category error message.

        Returns:
            Formatted error message
        """
        return (
            "❌ I didn't recognize that item type.\n\n"
            "Please try again with: bike, phone, laptop, or car"
        )

    def format_location_prompt(self) -> str:
        """Format generic location prompt.

        Returns:
            Formatted location prompt
        """
        return (
            "📍 Where was it last seen or stolen?\n\n"
            "You can either:\n"
            "• Type a location (e.g., 'Main Street, downtown')\n"
            "• Send your current location\n"
            "• Type 'skip' if you don't know"
        )

    def format_checking_location_prompt(self) -> str:
        """Format location prompt for checking flow.

        Returns:
            Formatted location prompt with skip option
        """
        return (
            "📍 Where was it last seen or stolen?\n\n"
            "You can either:\n"
            "• Type a location (e.g., 'Main Street, downtown')\n"
            "• Send your current location\n"
            "• Type 'skip' if you don't know"
        )

    def format_reporting_location_prompt(self) -> str:
        """Format location prompt for reporting flow.

        Returns:
            Formatted location prompt with unknown option
        """
        return (
            "📍 Where was it stolen?\n\n"
            "You can either:\n"
            "• Type the location\n"
            "• Send your location\n"
            "• Type 'unknown' if you're not sure"
        )

    def format_reporting_date_prompt(self) -> str:
        """Format date prompt for reporting flow.

        Returns:
            Formatted date prompt
        """
        return (
            "📅 When was it stolen?\n\n"
            "Examples:\n"
            "• 'today'\n"
            "• 'yesterday'\n"
            "• '3 days ago'\n"
            "• '15 January 2024'\n"
            "• 'last week'\n\n"
            "Type 'unknown' if you're not sure"
        )

    def format_invalid_date(self) -> str:
        """Format invalid date error message.

        Returns:
            Formatted error message
        """
        return (
            "❌ I didn't understand that date.\n\n"
            "Please try again with formats like:\n"
            "• 'today' or 'yesterday'\n"
            "• '2 days ago'\n"
            "• '15 Jan 2024'\n\n"
            "Or type 'unknown' if you're not sure"
        )

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
            return (
                f"🔍 Search complete!\n\n"
                f"Found {match_count} potential match{'es' if match_count != 1 else ''}.\n"
                "We'll send details in the next message.\n\n"
                "Send any message to start a new search."
            )
        else:
            return (
                "🔍 Searching for matches...\n\n"
                "No stolen items found matching your description.\n\n"
                "Send any message to start a new search."
            )

    def format_reporting_category_prompt(self) -> str:
        """Format prompt for reporting category.

        Returns:
            Formatted reporting category prompt
        """
        return (
            "📝 Report stolen item\n\n"
            "What type of item was stolen?\n"
            "Examples: bike, phone, laptop, car\n\n"
            "Type 'cancel' to go back."
        )

    def format_reporting_confirmation(self, category: ItemCategory) -> str:
        """Format reporting category confirmation.

        Args:
            category: Confirmed item category

        Returns:
            Formatted confirmation message
        """
        return (
            f"✅ Reporting stolen: {category.value}\n\n"
            "Please describe the item in detail:\n"
            "Include: brand, model, color, serial number, any unique features"
        )

    def format_reporting_complete(self) -> str:
        """Format reporting flow completion message.

        Returns:
            Formatted completion message
        """
        return (
            "✅ Thank you for reporting!\n\n"
            "Your stolen item has been recorded.\n"
            "We'll notify you if there are any matches.\n\n"
            "Send any message to make another report."
        )

    def format_main_menu_invalid_choice(self) -> str:
        """Format invalid main menu choice message.

        Returns:
            Formatted error message
        """
        return (
            "Please choose an option:\n"
            "1️⃣ Check if an item is stolen\n"
            "2️⃣ Report a stolen item\n\n"
            "Type 'cancel' to exit."
        )

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
        if not buttons:
            raise ValueError("At least 1 button required")
        if len(buttons) > 3:
            raise ValueError("Maximum 3 buttons allowed")

        # Validate button title lengths (Meta API limit: 20 characters)
        for button in buttons:
            if len(button["title"]) > 20:
                raise ValueError(
                    f"Button title '{button['title']}' cannot exceed 20 characters"
                )

        action_buttons = [
            {"type": "reply", "reply": {"id": btn["id"], "title": btn["title"]}}
            for btn in buttons
        ]

        return {
            "type": "interactive",
            "interactive": {
                "type": "button",
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
        if not sections:
            raise ValueError("At least 1 section required")
        if len(sections) > 10:
            raise ValueError("Maximum 10 sections allowed")

        total_rows = sum(len(section.get("rows", [])) for section in sections)
        if total_rows > 10:
            raise ValueError("Maximum 10 rows allowed across all sections")

        interactive: dict[str, Any] = {
            "type": "list",
            "body": {"text": body},
            "action": {"button": button_text, "sections": sections},
        }

        if header:
            interactive["header"] = {"type": "text", "text": header}

        return {"type": "interactive", "interactive": interactive}

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
            button_text="Select Category",
            sections=sections,
        )

    def build_welcome_buttons(self) -> dict[str, Any]:
        """Build welcome/main menu buttons.

        Returns:
            Dict with Meta WhatsApp Cloud API interactive button message
        """
        buttons = [
            {"id": "check_item", "title": "Check Item"},
            {"id": "report_item", "title": "Report Item"},
        ]

        return self.build_reply_buttons(
            body="👋 Welcome to Is It Stolen!\n\nWhat would you like to do?",
            buttons=buttons,
        )
