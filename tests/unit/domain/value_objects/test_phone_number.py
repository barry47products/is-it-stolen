"""Tests for PhoneNumber value object."""

from unittest.mock import MagicMock, patch

import pytest

from src.domain.value_objects.phone_number import PhoneNumber

pytestmark = pytest.mark.unit


class TestPhoneNumber:
    """Test suite for PhoneNumber value object."""

    def test_creates_phone_number_with_valid_e164_format(self) -> None:
        """Should create PhoneNumber with valid E.164 format."""
        phone = PhoneNumber("+447911123456")
        assert phone.value == "+447911123456"

    def test_creates_phone_number_with_us_number(self) -> None:
        """Should create PhoneNumber with US number."""
        phone = PhoneNumber("+12025551234")
        assert phone.value == "+12025551234"

    def test_creates_phone_number_with_south_african_number(self) -> None:
        """Should create PhoneNumber with South African number."""
        phone = PhoneNumber("+27821234567")
        assert phone.value == "+27821234567"

    def test_phone_number_is_immutable(self) -> None:
        """Should not allow modification after creation."""
        phone = PhoneNumber("+447911123456")
        with pytest.raises(AttributeError):
            phone.value = "+12025551234"  # type: ignore[misc]

    def test_rejects_phone_number_without_plus(self) -> None:
        """Should reject phone number missing + prefix."""
        with pytest.raises(ValueError, match="Invalid phone number"):
            PhoneNumber("447700900123")

    def test_rejects_invalid_phone_number_format(self) -> None:
        """Should reject invalid phone number format."""
        with pytest.raises(ValueError, match="Invalid phone number"):
            PhoneNumber("+123")

    def test_rejects_phone_number_with_letters(self) -> None:
        """Should reject phone number containing letters."""
        with pytest.raises(ValueError, match="Invalid phone number"):
            PhoneNumber("+44ABC123")

    def test_rejects_empty_phone_number(self) -> None:
        """Should reject empty phone number."""
        with pytest.raises(ValueError, match="Invalid phone number"):
            PhoneNumber("")

    def test_extracts_country_code_from_uk_number(self) -> None:
        """Should extract country code from UK number."""
        phone = PhoneNumber("+447911123456")
        assert phone.country_code == 44

    def test_extracts_country_code_from_us_number(self) -> None:
        """Should extract country code from US number."""
        phone = PhoneNumber("+12025551234")
        assert phone.country_code == 1

    def test_extracts_country_code_from_south_african_number(self) -> None:
        """Should extract country code from South African number."""
        phone = PhoneNumber("+27821234567")
        assert phone.country_code == 27

    def test_provides_formatted_international_display(self) -> None:
        """Should provide internationally formatted display."""
        phone = PhoneNumber("+447911123456")
        formatted = phone.formatted
        assert formatted.startswith("+44")
        assert " " in formatted  # Should have spaces

    def test_phone_number_equality(self) -> None:
        """Should support equality comparison."""
        phone1 = PhoneNumber("+447911123456")
        phone2 = PhoneNumber("+447911123456")
        phone3 = PhoneNumber("+12025551234")

        assert phone1 == phone2
        assert phone1 != phone3

    def test_phone_number_repr(self) -> None:
        """Should have readable string representation."""
        phone = PhoneNumber("+447911123456")
        assert "+447911123456" in repr(phone)

    def test_normalizes_phone_number_with_spaces(self) -> None:
        """Should normalize phone number with spaces."""
        phone = PhoneNumber("+44 7911 123 456")
        assert phone.value == "+447911123456"

    def test_normalizes_phone_number_with_dashes(self) -> None:
        """Should normalize phone number with dashes."""
        phone = PhoneNumber("+44-7911-123-456")
        assert phone.value == "+447911123456"

    def test_country_code_raises_value_error_when_missing(self) -> None:
        """Should raise ValueError if country code is None (edge case)."""
        phone = PhoneNumber("+447911123456")

        # Mock phonenumbers.parse to return object with None country_code
        mock_parsed = MagicMock()
        mock_parsed.country_code = None

        with patch(
            "src.domain.value_objects.phone_number.phonenumbers.parse"
        ) as mock_parse:
            mock_parse.return_value = mock_parsed
            with pytest.raises(
                ValueError, match="Valid phone number must have country code"
            ):
                _ = phone.country_code
