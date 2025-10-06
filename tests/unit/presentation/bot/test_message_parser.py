"""Tests for message parser."""

from datetime import UTC, datetime, timedelta

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

    def test_parse_date_today(self) -> None:
        """Test parsing 'today' returns current date."""
        # Arrange
        parser = MessageParser()
        now = datetime.now(UTC)

        # Act
        result = parser.parse_date("today")

        # Assert
        assert result is not None
        assert result.date() == now.date()

    def test_parse_date_yesterday(self) -> None:
        """Test parsing 'yesterday' returns yesterday's date."""
        # Arrange
        parser = MessageParser()
        yesterday = datetime.now(UTC) - timedelta(days=1)

        # Act
        result = parser.parse_date("yesterday")

        # Assert
        assert result is not None
        assert result.date() == yesterday.date()

    def test_parse_date_days_ago(self) -> None:
        """Test parsing 'X days ago' format."""
        # Arrange
        parser = MessageParser()
        three_days_ago = datetime.now(UTC) - timedelta(days=3)

        # Act
        result = parser.parse_date("3 days ago")

        # Assert
        assert result is not None
        assert result.date() == three_days_ago.date()

    def test_parse_date_specific_date(self) -> None:
        """Test parsing specific date format."""
        # Arrange
        parser = MessageParser()

        # Act
        result = parser.parse_date("15 January 2024")

        # Assert
        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_parse_date_last_week(self) -> None:
        """Test parsing 'last week'."""
        # Arrange
        parser = MessageParser()
        last_week = datetime.now(UTC) - timedelta(weeks=1)

        # Act
        result = parser.parse_date("last week")

        # Assert
        assert result is not None
        # Allow some tolerance since "last week" is approximate
        assert abs((result.date() - last_week.date()).days) <= 2

    def test_parse_date_skip_returns_now(self) -> None:
        """Test parsing 'skip' returns current datetime."""
        # Arrange
        parser = MessageParser()
        now = datetime.now(UTC)

        # Act
        result = parser.parse_date("skip")

        # Assert
        assert result is not None
        assert result.date() == now.date()

    def test_parse_date_unknown_returns_now(self) -> None:
        """Test parsing 'unknown' returns current datetime."""
        # Arrange
        parser = MessageParser()
        now = datetime.now(UTC)

        # Act
        result = parser.parse_date("unknown")

        # Assert
        assert result is not None
        assert result.date() == now.date()

    def test_parse_date_dont_know_returns_now(self) -> None:
        """Test parsing 'don't know' returns current datetime."""
        # Arrange
        parser = MessageParser()
        now = datetime.now(UTC)

        # Act
        result = parser.parse_date("don't know")

        # Assert
        assert result is not None
        assert result.date() == now.date()

    def test_parse_date_future_date_returns_none(self) -> None:
        """Test parsing future date returns None."""
        # Arrange
        parser = MessageParser()
        future_date = datetime.now(UTC) + timedelta(days=7)
        future_str = future_date.strftime("%d %B %Y")

        # Act
        result = parser.parse_date(future_str)

        # Assert
        assert result is None

    def test_parse_date_invalid_text_returns_none(self) -> None:
        """Test parsing invalid text returns None."""
        # Arrange
        parser = MessageParser()

        # Act
        result = parser.parse_date("not a date at all xyz")

        # Assert
        assert result is None

    def test_parse_date_returns_utc_timezone(self) -> None:
        """Test parsed dates are in UTC timezone."""
        # Arrange
        parser = MessageParser()

        # Act
        result = parser.parse_date("yesterday")

        # Assert
        assert result is not None
        assert result.tzinfo is not None
        # Check if datetime is timezone-aware (UTC or has offset)

    def test_parse_date_whitespace_handling(self) -> None:
        """Test parse_date handles whitespace correctly."""
        # Arrange
        parser = MessageParser()

        # Act
        result = parser.parse_date("  today  ")

        # Assert
        assert result is not None
        assert result.date() == datetime.now(UTC).date()

    def test_parse_date_too_long_returns_none(self) -> None:
        """Test parse_date rejects text longer than 100 characters."""
        # Arrange
        parser = MessageParser()
        long_text = "a" * 101

        # Act
        result = parser.parse_date(long_text)

        # Assert
        assert result is None

    def test_parse_date_no_date_indicators_returns_none(self) -> None:
        """Test parse_date rejects text with no date indicators."""
        # Arrange
        parser = MessageParser()

        # Act
        result = parser.parse_date("hello world")

        # Assert
        assert result is None

    def test_parse_date_unparseable_but_has_indicators(self, mocker) -> None:  # type: ignore[no-untyped-def]
        """Test parse_date when text has date indicators but can't be parsed."""
        # Arrange
        parser = MessageParser()

        # Mock dateparser to return None (simulate unparseable date)
        mocker.patch("dateparser.parse", return_value=None)

        # Act - Text has month keyword but dateparser can't parse it
        result = parser.parse_date("jan xyz abc")

        # Assert
        assert result is None

    def test_parse_date_returns_none_for_non_datetime_result(self, mocker) -> None:  # type: ignore[no-untyped-def]
        """Test parse_date when dateparser returns non-datetime object."""
        # Arrange
        parser = MessageParser()

        # Mock dateparser to return a non-datetime object (edge case)
        mocker.patch("dateparser.parse", return_value="not a datetime")

        # Act
        result = parser.parse_date("yesterday")

        # Assert
        assert result is None
