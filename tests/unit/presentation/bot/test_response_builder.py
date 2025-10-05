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
