"""Tests for message parser."""

import pytest

from src.domain.value_objects.item_category import ItemCategory
from src.presentation.bot.message_parser import MessageParser


@pytest.mark.unit
class TestMessageParser:
    """Test message parser."""

    def test_parse_category_from_bicycle_keywords(self) -> None:
        """Test parsing bicycle category from keywords."""
        # Arrange
        parser = MessageParser()

        # Act & Assert
        assert parser.parse_category("bike") == ItemCategory.BICYCLE
        assert parser.parse_category("bicycle") == ItemCategory.BICYCLE
        assert parser.parse_category("I lost my bike") == ItemCategory.BICYCLE

    def test_parse_category_from_phone_keywords(self) -> None:
        """Test parsing phone category from keywords."""
        # Arrange
        parser = MessageParser()

        # Act & Assert
        assert parser.parse_category("phone") == ItemCategory.PHONE
        assert parser.parse_category("smartphone") == ItemCategory.PHONE
        assert parser.parse_category("my iPhone was stolen") == ItemCategory.PHONE

    def test_parse_category_from_laptop_keywords(self) -> None:
        """Test parsing laptop category from keywords."""
        # Arrange
        parser = MessageParser()

        # Act & Assert
        assert parser.parse_category("laptop") == ItemCategory.LAPTOP
        assert parser.parse_category("computer") == ItemCategory.LAPTOP
        assert parser.parse_category("MacBook") == ItemCategory.LAPTOP

    def test_parse_category_returns_none_when_no_match(self) -> None:
        """Test parsing category returns None when no keywords match."""
        # Arrange
        parser = MessageParser()

        # Act
        result = parser.parse_category("something random")

        # Assert
        assert result is None

    def test_parse_category_case_insensitive(self) -> None:
        """Test category parsing is case insensitive."""
        # Arrange
        parser = MessageParser()

        # Act & Assert
        assert parser.parse_category("BIKE") == ItemCategory.BICYCLE
        assert parser.parse_category("BiKe") == ItemCategory.BICYCLE

    def test_extract_brand_and_model_simple(self) -> None:
        """Test extracting brand and model from simple text."""
        # Arrange
        parser = MessageParser()

        # Act
        result = parser.extract_brand_model("Red Trek bike")

        # Assert
        assert "trek" in result.lower()

    def test_extract_brand_and_model_with_model_number(self) -> None:
        """Test extracting brand and model with model number."""
        # Arrange
        parser = MessageParser()

        # Act
        result = parser.extract_brand_model("iPhone 13 Pro Max")

        # Assert
        assert "iphone" in result.lower()
        assert "13" in result

    def test_extract_brand_and_model_from_sentence(self) -> None:
        """Test extracting brand and model from full sentence."""
        # Arrange
        parser = MessageParser()

        # Act
        result = parser.extract_brand_model(
            "My silver MacBook Pro 2021 was stolen yesterday"
        )

        # Assert
        assert "macbook" in result.lower()
        assert "pro" in result.lower()

    def test_extract_brand_and_model_returns_empty_when_none(self) -> None:
        """Test extracting brand returns empty when none found."""
        # Arrange
        parser = MessageParser()

        # Act
        result = parser.extract_brand_model("it was red")

        # Assert
        assert result == ""

    def test_parse_location_from_text(self) -> None:
        """Test parsing location from text description."""
        # Arrange
        parser = MessageParser()

        # Act
        result = parser.parse_location_text("near Main Street, downtown")

        # Assert
        assert result == "near Main Street, downtown"

    def test_parse_location_extracts_from_sentence(self) -> None:
        """Test parsing location extracts from sentence."""
        # Arrange
        parser = MessageParser()

        # Act
        result = parser.parse_location_text(
            "It was stolen at the parking lot on Baker Street"
        )

        # Assert
        assert "baker street" in result.lower() or "parking lot" in result.lower()

    def test_parse_category_handles_invalid_category_name(self) -> None:
        """Test parsing category handles invalid category names gracefully."""
        # Arrange
        parser = MessageParser()
        # Manually add an invalid category to the keywords
        parser.category_keywords["INVALID_CATEGORY"] = ["invalid"]

        # Act
        result = parser.parse_category("invalid keyword")

        # Assert
        assert result is None  # Should return None for invalid category names
