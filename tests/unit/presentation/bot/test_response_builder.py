"""Tests for response builder."""

import pytest

from src.domain.value_objects.item_category import ItemCategory
from src.presentation.bot.response_builder import ResponseBuilder


@pytest.mark.unit
class TestResponseBuilder:
    """Test response builder."""

    def test_format_welcome_message(self) -> None:
        """Test format welcome message."""
        # Arrange
        builder = ResponseBuilder()

        # Act
        response = builder.format_welcome()

        # Assert
        assert "welcome" in response.lower()
        assert "is it stolen" in response.lower()
        assert "1" in response
        assert "2" in response
        assert "check" in response.lower()
        assert "report" in response.lower()

    def test_format_cancel_message(self) -> None:
        """Test format cancel message."""
        # Arrange
        builder = ResponseBuilder()

        # Act
        response = builder.format_cancel()

        # Assert
        assert "cancel" in response.lower()
        assert "start again" in response.lower()

    def test_format_checking_category_prompt(self) -> None:
        """Test format checking category prompt."""
        # Arrange
        builder = ResponseBuilder()

        # Act
        response = builder.format_checking_category_prompt()

        # Assert
        assert "check" in response.lower()
        assert "type" in response.lower()
        assert "bike" in response.lower() or "phone" in response.lower()

    def test_format_checking_category_confirmation(self) -> None:
        """Test format category confirmation."""
        # Arrange
        builder = ResponseBuilder()
        category = ItemCategory.BICYCLE

        # Act
        response = builder.format_category_confirmation(category)

        # Assert
        assert "bicycle" in response.lower()
        assert "describe" in response.lower()

    def test_format_invalid_category_error(self) -> None:
        """Test format invalid category error."""
        # Arrange
        builder = ResponseBuilder()

        # Act
        response = builder.format_invalid_category()

        # Assert
        assert "didn't recognize" in response.lower() or "invalid" in response.lower()
        assert "try again" in response.lower()

    def test_format_location_prompt(self) -> None:
        """Test format location prompt."""
        # Arrange
        builder = ResponseBuilder()

        # Act
        response = builder.format_location_prompt()

        # Assert
        assert "location" in response.lower() or "where" in response.lower()
        assert "skip" in response.lower() or "unknown" in response.lower()

    def test_format_checking_complete_no_matches(self) -> None:
        """Test format checking complete with no matches."""
        # Arrange
        builder = ResponseBuilder()

        # Act
        response = builder.format_checking_complete(matches_found=False)

        # Assert
        assert "no" in response.lower() or "not found" in response.lower()
        assert "match" in response.lower()

    def test_format_checking_complete_with_matches(self) -> None:
        """Test format checking complete with matches."""
        # Arrange
        builder = ResponseBuilder()

        # Act
        response = builder.format_checking_complete(matches_found=True, match_count=3)

        # Assert
        assert "found" in response.lower() or "match" in response.lower()
        assert "3" in response

    def test_format_reporting_category_prompt(self) -> None:
        """Test format reporting category prompt."""
        # Arrange
        builder = ResponseBuilder()

        # Act
        response = builder.format_reporting_category_prompt()

        # Assert
        assert "report" in response.lower()
        assert "stolen" in response.lower()
        assert "type" in response.lower()

    def test_format_reporting_category_confirmation(self) -> None:
        """Test format reporting category confirmation."""
        # Arrange
        builder = ResponseBuilder()
        category = ItemCategory.PHONE

        # Act
        response = builder.format_reporting_confirmation(category)

        # Assert
        assert "phone" in response.lower()
        assert "detail" in response.lower() or "describe" in response.lower()

    def test_format_reporting_complete(self) -> None:
        """Test format reporting complete message."""
        # Arrange
        builder = ResponseBuilder()

        # Act
        response = builder.format_reporting_complete()

        # Assert
        assert "thank you" in response.lower() or "thanks" in response.lower()
        assert "report" in response.lower()
        assert "recorded" in response.lower() or "saved" in response.lower()

    def test_format_main_menu_invalid_choice(self) -> None:
        """Test format main menu invalid choice."""
        # Arrange
        builder = ResponseBuilder()

        # Act
        response = builder.format_main_menu_invalid_choice()

        # Assert
        assert "choose" in response.lower() or "select" in response.lower()
        assert "1" in response
        assert "2" in response

    def test_format_checking_location_prompt_uses_skip(self) -> None:
        """Test checking location prompt mentions skip."""
        # Arrange
        builder = ResponseBuilder()

        # Act
        response = builder.format_checking_location_prompt()

        # Assert
        assert "skip" in response.lower()

    def test_format_reporting_location_prompt_uses_unknown(self) -> None:
        """Test reporting location prompt mentions unknown."""
        # Arrange
        builder = ResponseBuilder()

        # Act
        response = builder.format_reporting_location_prompt()

        # Assert
        assert "unknown" in response.lower()

    def test_all_messages_respect_whatsapp_limits(self) -> None:
        """Test all messages are under WhatsApp length limit."""
        # Arrange
        builder = ResponseBuilder()
        max_length = 4096  # WhatsApp message limit

        # Act & Assert - test all public format methods
        assert len(builder.format_welcome()) <= max_length
        assert len(builder.format_cancel()) <= max_length
        assert len(builder.format_checking_category_prompt()) <= max_length
        assert (
            len(builder.format_category_confirmation(ItemCategory.BICYCLE))
            <= max_length
        )
        assert len(builder.format_invalid_category()) <= max_length
        assert len(builder.format_location_prompt()) <= max_length
        assert len(builder.format_checking_complete(False)) <= max_length
        assert len(builder.format_reporting_category_prompt()) <= max_length
        assert (
            len(builder.format_reporting_confirmation(ItemCategory.PHONE)) <= max_length
        )
        assert len(builder.format_reporting_complete()) <= max_length
        assert len(builder.format_main_menu_invalid_choice()) <= max_length

    def test_messages_contain_emojis_for_visual_appeal(self) -> None:
        """Test messages use emojis appropriately."""
        # Arrange
        builder = ResponseBuilder()

        # Act & Assert - check key messages have emojis
        assert any(
            emoji in builder.format_welcome() for emoji in ["👋", "🔍", "📝", "1️⃣", "2️⃣"]
        )
        assert "✅" in builder.format_category_confirmation(ItemCategory.BICYCLE)
        assert "❌" in builder.format_invalid_category()
        assert "📍" in builder.format_location_prompt()
        assert "🔍" in builder.format_checking_complete(False)
        assert "✅" in builder.format_reporting_complete()


class TestBuildReplyButtons:
    """Tests for building reply button interactive messages."""

    def test_builds_single_button(self) -> None:
        """Test building message with single reply button."""
        builder = ResponseBuilder()

        result = builder.build_reply_buttons(
            body="Choose an option:", buttons=[{"id": "btn_1", "title": "Option 1"}]
        )

        assert result["type"] == "interactive"
        assert result["interactive"]["type"] == "button"
        assert result["interactive"]["body"]["text"] == "Choose an option:"
        assert len(result["interactive"]["action"]["buttons"]) == 1
        assert result["interactive"]["action"]["buttons"][0]["type"] == "reply"
        assert result["interactive"]["action"]["buttons"][0]["reply"]["id"] == "btn_1"
        assert (
            result["interactive"]["action"]["buttons"][0]["reply"]["title"]
            == "Option 1"
        )

    def test_builds_three_buttons(self) -> None:
        """Test building message with three reply buttons (maximum)."""
        builder = ResponseBuilder()

        buttons = [
            {"id": "check", "title": "Check Item"},
            {"id": "report", "title": "Report Item"},
            {"id": "cancel", "title": "Cancel"},
        ]

        result = builder.build_reply_buttons(body="Main Menu", buttons=buttons)

        assert len(result["interactive"]["action"]["buttons"]) == 3
        assert result["interactive"]["action"]["buttons"][0]["reply"]["id"] == "check"
        assert result["interactive"]["action"]["buttons"][1]["reply"]["id"] == "report"
        assert result["interactive"]["action"]["buttons"][2]["reply"]["id"] == "cancel"

    def test_raises_error_for_more_than_three_buttons(self) -> None:
        """Test ValueError raised when more than 3 buttons provided."""
        builder = ResponseBuilder()

        buttons = [
            {"id": f"btn_{i}", "title": f"Button {i}"}
            for i in range(4)  # 4 buttons
        ]

        with pytest.raises(ValueError, match="Maximum 3 buttons allowed"):
            builder.build_reply_buttons(body="Too many buttons", buttons=buttons)

    def test_raises_error_for_empty_buttons(self) -> None:
        """Test ValueError raised when no buttons provided."""
        builder = ResponseBuilder()

        with pytest.raises(ValueError, match="At least 1 button required"):
            builder.build_reply_buttons(body="No buttons", buttons=[])

    def test_validates_button_title_length(self) -> None:
        """Test validation of button title length (max 20 chars)."""
        builder = ResponseBuilder()

        long_title = "This is a very long button title that exceeds twenty characters"
        buttons = [{"id": "btn_1", "title": long_title}]

        with pytest.raises(ValueError, match=r"Button title.*exceed 20 characters"):
            builder.build_reply_buttons(body="Test", buttons=buttons)

    def test_returns_dict_matching_meta_api_spec(self) -> None:
        """Test returned dict matches Meta's WhatsApp Cloud API specification."""
        builder = ResponseBuilder()

        buttons = [{"id": "yes", "title": "Yes"}, {"id": "no", "title": "No"}]

        result = builder.build_reply_buttons(
            body="Do you want to continue?", buttons=buttons
        )

        # Verify exact structure per Meta API spec
        assert "type" in result
        assert "interactive" in result
        assert "type" in result["interactive"]
        assert "body" in result["interactive"]
        assert "text" in result["interactive"]["body"]
        assert "action" in result["interactive"]
        assert "buttons" in result["interactive"]["action"]
        for btn in result["interactive"]["action"]["buttons"]:
            assert btn["type"] == "reply"
            assert "reply" in btn
            assert "id" in btn["reply"]
            assert "title" in btn["reply"]


class TestBuildListMessage:
    """Tests for building list interactive messages."""

    def test_builds_list_with_single_section(self) -> None:
        """Test building list message with single section."""
        builder = ResponseBuilder()

        sections = [
            {
                "title": "Categories",
                "rows": [
                    {
                        "id": "bicycle",
                        "title": "Bicycle",
                        "description": "Two-wheeled vehicle",
                    },
                    {"id": "phone", "title": "Phone", "description": "Mobile phone"},
                ],
            }
        ]

        result = builder.build_list_message(
            body="Choose a category:",
            button_text="View Categories",
            sections=sections,
        )

        assert result["type"] == "interactive"
        assert result["interactive"]["type"] == "list"
        assert result["interactive"]["body"]["text"] == "Choose a category:"
        assert result["interactive"]["action"]["button"] == "View Categories"
        assert len(result["interactive"]["action"]["sections"]) == 1
        assert result["interactive"]["action"]["sections"][0]["title"] == "Categories"
        assert len(result["interactive"]["action"]["sections"][0]["rows"]) == 2

    def test_builds_list_with_multiple_sections(self) -> None:
        """Test building list message with multiple sections."""
        builder = ResponseBuilder()

        sections = [
            {
                "title": "Vehicles",
                "rows": [
                    {"id": "bicycle", "title": "Bicycle"},
                    {"id": "car", "title": "Car"},
                ],
            },
            {
                "title": "Electronics",
                "rows": [
                    {"id": "phone", "title": "Phone"},
                    {"id": "laptop", "title": "Laptop"},
                ],
            },
        ]

        result = builder.build_list_message(
            body="Select category:", button_text="Choose", sections=sections
        )

        assert len(result["interactive"]["action"]["sections"]) == 2
        assert result["interactive"]["action"]["sections"][0]["title"] == "Vehicles"
        assert result["interactive"]["action"]["sections"][1]["title"] == "Electronics"

    def test_builds_list_with_optional_header(self) -> None:
        """Test building list message with optional header."""
        builder = ResponseBuilder()

        sections = [
            {
                "title": "Options",
                "rows": [{"id": "opt_1", "title": "Option 1"}],
            }
        ]

        result = builder.build_list_message(
            body="Choose:", button_text="Select", sections=sections, header="Main Menu"
        )

        assert "header" in result["interactive"]
        assert result["interactive"]["header"]["type"] == "text"
        assert result["interactive"]["header"]["text"] == "Main Menu"

    def test_raises_error_for_more_than_ten_sections(self) -> None:
        """Test ValueError raised when more than 10 sections provided."""
        builder = ResponseBuilder()

        sections = [
            {"title": f"Section {i}", "rows": [{"id": f"r_{i}", "title": f"Row {i}"}]}
            for i in range(11)  # 11 sections
        ]

        with pytest.raises(ValueError, match="Maximum 10 sections allowed"):
            builder.build_list_message(
                body="Test", button_text="View", sections=sections
            )

    def test_raises_error_for_more_than_ten_rows_total(self) -> None:
        """Test ValueError raised when total rows exceed 10."""
        builder = ResponseBuilder()

        sections = [
            {
                "title": "Section 1",
                "rows": [
                    {"id": f"row_{i}", "title": f"Row {i}"} for i in range(6)
                ],  # 6 rows
            },
            {
                "title": "Section 2",
                "rows": [
                    {"id": f"row2_{i}", "title": f"Row {i}"} for i in range(5)
                ],  # 5 rows = 11 total
            },
        ]

        with pytest.raises(ValueError, match="Maximum 10 rows allowed"):
            builder.build_list_message(
                body="Test", button_text="View", sections=sections
            )

    def test_raises_error_for_empty_sections(self) -> None:
        """Test ValueError raised when no sections provided."""
        builder = ResponseBuilder()

        with pytest.raises(ValueError, match="At least 1 section required"):
            builder.build_list_message(body="Test", button_text="View", sections=[])

    def test_returns_dict_matching_meta_api_spec(self) -> None:
        """Test returned dict matches Meta's WhatsApp Cloud API specification."""
        builder = ResponseBuilder()

        sections = [
            {
                "title": "Categories",
                "rows": [
                    {"id": "cat1", "title": "Category 1", "description": "Desc 1"}
                ],
            }
        ]

        result = builder.build_list_message(
            body="Choose:", button_text="Select", sections=sections
        )

        # Verify exact structure per Meta API spec
        assert "type" in result
        assert "interactive" in result
        assert "type" in result["interactive"]
        assert "body" in result["interactive"]
        assert "text" in result["interactive"]["body"]
        assert "action" in result["interactive"]
        assert "button" in result["interactive"]["action"]
        assert "sections" in result["interactive"]["action"]
        for section in result["interactive"]["action"]["sections"]:
            assert "title" in section
            assert "rows" in section
            for row in section["rows"]:
                assert "id" in row
                assert "title" in row


class TestBuildCategoryList:
    """Tests for building category selection list."""

    def test_builds_category_list_from_all_categories(self) -> None:
        """Test building list with all available item categories."""
        builder = ResponseBuilder()

        result = builder.build_category_list()

        assert result["type"] == "interactive"
        assert result["interactive"]["type"] == "list"
        assert result["interactive"]["body"]["text"] == "What type of item?"
        assert result["interactive"]["action"]["button"] == "Select Category"

        # Should have at least the 4 main categories
        sections = result["interactive"]["action"]["sections"]
        assert len(sections) > 0

        all_rows = []
        for section in sections:
            all_rows.extend(section["rows"])

        # Check main categories are present
        category_ids = [row["id"] for row in all_rows]
        assert "bicycle" in category_ids
        assert "phone" in category_ids
        assert "laptop" in category_ids
        assert "car" in category_ids


class TestBuildWelcomeButtons:
    """Tests for building welcome/main menu buttons."""

    def test_builds_welcome_buttons_with_check_and_report(self) -> None:
        """Test building welcome message with Check and Report buttons."""
        builder = ResponseBuilder()

        result = builder.build_welcome_buttons()

        assert result["type"] == "interactive"
        assert result["interactive"]["type"] == "button"
        assert "welcome" in result["interactive"]["body"]["text"].lower()
        assert len(result["interactive"]["action"]["buttons"]) == 2

        # Check button IDs and titles
        buttons = result["interactive"]["action"]["buttons"]
        button_ids = [btn["reply"]["id"] for btn in buttons]
        button_titles = [btn["reply"]["title"] for btn in buttons]

        assert "check_item" in button_ids
        assert "report_item" in button_ids
        assert "Check Item" in button_titles
        assert "Report Item" in button_titles
