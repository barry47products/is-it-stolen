"""Unit tests for ConversionRate value object."""

import pytest

from src.domain.value_objects.conversion_rate import ConversionRate


class TestConversionRate:
    """Test suite for ConversionRate value object."""

    def test_creates_valid_conversion_rate(self) -> None:
        """Test creating ConversionRate with valid rate."""
        # Arrange
        rate = 0.75

        # Act
        conversion_rate = ConversionRate(rate)

        # Assert
        assert conversion_rate.value == 0.75

    def test_accepts_zero_rate(self) -> None:
        """Test ConversionRate accepts 0.0."""
        # Act
        conversion_rate = ConversionRate(0.0)

        # Assert
        assert conversion_rate.value == 0.0

    def test_accepts_one_hundred_percent_rate(self) -> None:
        """Test ConversionRate accepts 1.0."""
        # Act
        conversion_rate = ConversionRate(1.0)

        # Assert
        assert conversion_rate.value == 1.0

    def test_rejects_negative_rate(self) -> None:
        """Test ConversionRate rejects negative values."""
        # Act & Assert
        with pytest.raises(ValueError, match=r"between 0\.0 and 1\.0"):
            ConversionRate(-0.1)

    def test_rejects_rate_above_one(self) -> None:
        """Test ConversionRate rejects values above 1.0."""
        # Act & Assert
        with pytest.raises(ValueError, match=r"between 0\.0 and 1\.0"):
            ConversionRate(1.5)

    def test_conversion_rate_is_immutable(self) -> None:
        """Test that ConversionRate is immutable."""
        # Arrange
        conversion_rate = ConversionRate(0.5)

        # Act & Assert
        with pytest.raises((AttributeError, TypeError)):  # FrozenInstanceError
            conversion_rate.value = 0.8  # type: ignore[misc]

    def test_to_percentage_string(self) -> None:
        """Test formatting as percentage string."""
        # Arrange
        conversion_rate = ConversionRate(0.756)

        # Act
        result = conversion_rate.to_percentage_string()

        # Assert
        assert result == "75.60%"

    def test_to_percentage_string_rounds_correctly(self) -> None:
        """Test percentage rounding."""
        # Arrange
        conversion_rate = ConversionRate(0.12345)

        # Act
        result = conversion_rate.to_percentage_string()

        # Assert
        assert result == "12.35%"

    def test_to_percentage_string_handles_zero(self) -> None:
        """Test formatting zero rate."""
        # Arrange
        conversion_rate = ConversionRate(0.0)

        # Act
        result = conversion_rate.to_percentage_string()

        # Assert
        assert result == "0.00%"

    def test_to_percentage_string_handles_one(self) -> None:
        """Test formatting 100% rate."""
        # Arrange
        conversion_rate = ConversionRate(1.0)

        # Act
        result = conversion_rate.to_percentage_string()

        # Assert
        assert result == "100.00%"

    def test_conversion_rates_with_same_value_are_equal(self) -> None:
        """Test equality of ConversionRates."""
        # Arrange
        rate1 = ConversionRate(0.5)
        rate2 = ConversionRate(0.5)

        # Act & Assert
        assert rate1 == rate2

    def test_conversion_rates_with_different_values_are_not_equal(self) -> None:
        """Test inequality of ConversionRates."""
        # Arrange
        rate1 = ConversionRate(0.5)
        rate2 = ConversionRate(0.6)

        # Act & Assert
        assert rate1 != rate2
