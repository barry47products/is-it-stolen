"""Unit tests for domain exceptions."""

import pytest

from src.domain.exceptions.domain_exceptions import (
    DomainError,
    InvalidItemCategoryError,
    InvalidLocationError,
    InvalidPhoneNumberError,
    ItemAlreadyRecoveredError,
    ItemNotFoundError,
)


class TestDomainError:
    """Test suite for base DomainError."""

    def test_creates_domain_error_with_message(self) -> None:
        """Should create DomainError with message."""
        # Arrange & Act
        error = DomainError("Something went wrong", code="DOMAIN_ERROR")

        # Assert
        assert str(error) == "Something went wrong"
        assert error.code == "DOMAIN_ERROR"
        assert isinstance(error, Exception)

    def test_domain_error_has_default_code(self) -> None:
        """Should have default error code if not provided."""
        # Arrange & Act
        error = DomainError("Error message")

        # Assert
        assert error.code == "DOMAIN_ERROR"


class TestInvalidLocationError:
    """Test suite for InvalidLocationError."""

    def test_creates_invalid_location_error(self) -> None:
        """Should create InvalidLocationError with message and code."""
        # Arrange & Act
        error = InvalidLocationError("Invalid latitude: 91.0")

        # Assert
        assert str(error) == "Invalid latitude: 91.0"
        assert error.code == "INVALID_LOCATION"
        assert isinstance(error, DomainError)

    def test_invalid_location_error_can_be_raised(self) -> None:
        """Should be able to raise and catch InvalidLocationError."""
        # Arrange & Act & Assert
        with pytest.raises(InvalidLocationError, match="Invalid coordinates"):
            raise InvalidLocationError("Invalid coordinates")


class TestInvalidPhoneNumberError:
    """Test suite for InvalidPhoneNumberError."""

    def test_creates_invalid_phone_number_error(self) -> None:
        """Should create InvalidPhoneNumberError with message and code."""
        # Arrange & Act
        error = InvalidPhoneNumberError("Invalid phone number: 123")

        # Assert
        assert str(error) == "Invalid phone number: 123"
        assert error.code == "INVALID_PHONE_NUMBER"
        assert isinstance(error, DomainError)

    def test_invalid_phone_number_error_can_be_raised(self) -> None:
        """Should be able to raise and catch InvalidPhoneNumberError."""
        # Arrange & Act & Assert
        with pytest.raises(InvalidPhoneNumberError, match="Missing country code"):
            raise InvalidPhoneNumberError("Missing country code")


class TestInvalidItemCategoryError:
    """Test suite for InvalidItemCategoryError."""

    def test_creates_invalid_item_category_error(self) -> None:
        """Should create InvalidItemCategoryError with message and code."""
        # Arrange & Act
        error = InvalidItemCategoryError("Unknown category: invalid")

        # Assert
        assert str(error) == "Unknown category: invalid"
        assert error.code == "INVALID_ITEM_CATEGORY"
        assert isinstance(error, DomainError)

    def test_invalid_item_category_error_can_be_raised(self) -> None:
        """Should be able to raise and catch InvalidItemCategoryError."""
        # Arrange & Act & Assert
        with pytest.raises(InvalidItemCategoryError, match="Unknown category"):
            raise InvalidItemCategoryError("Unknown category: xyz")


class TestItemNotFoundError:
    """Test suite for ItemNotFoundError."""

    def test_creates_item_not_found_error(self) -> None:
        """Should create ItemNotFoundError with message and code."""
        # Arrange & Act
        error = ItemNotFoundError("Item with ID abc123 not found")

        # Assert
        assert str(error) == "Item with ID abc123 not found"
        assert error.code == "ITEM_NOT_FOUND"
        assert isinstance(error, DomainError)

    def test_item_not_found_error_can_be_raised(self) -> None:
        """Should be able to raise and catch ItemNotFoundError."""
        # Arrange & Act & Assert
        with pytest.raises(ItemNotFoundError, match="not found"):
            raise ItemNotFoundError("Item not found")


class TestItemAlreadyRecoveredError:
    """Test suite for ItemAlreadyRecoveredError."""

    def test_creates_item_already_recovered_error(self) -> None:
        """Should create ItemAlreadyRecoveredError with message and code."""
        # Arrange & Act
        error = ItemAlreadyRecoveredError("Item is already marked as recovered")

        # Assert
        assert str(error) == "Item is already marked as recovered"
        assert error.code == "ITEM_ALREADY_RECOVERED"
        assert isinstance(error, DomainError)

    def test_item_already_recovered_error_can_be_raised(self) -> None:
        """Should be able to raise and catch ItemAlreadyRecoveredError."""
        # Arrange & Act & Assert
        with pytest.raises(ItemAlreadyRecoveredError, match="already recovered"):
            raise ItemAlreadyRecoveredError("Item already recovered")


class TestExceptionHierarchy:
    """Test suite for exception hierarchy."""

    def test_all_domain_exceptions_extend_domain_error(self) -> None:
        """Should verify all exceptions extend DomainError."""
        # Arrange & Act
        exceptions = [
            InvalidLocationError("test"),
            InvalidPhoneNumberError("test"),
            InvalidItemCategoryError("test"),
            ItemNotFoundError("test"),
            ItemAlreadyRecoveredError("test"),
        ]

        # Assert
        for exc in exceptions:
            assert isinstance(exc, DomainError)
            assert isinstance(exc, Exception)

    def test_domain_error_can_catch_all_domain_exceptions(self) -> None:
        """Should be able to catch all domain exceptions with DomainError."""
        # Arrange & Act & Assert
        with pytest.raises(DomainError):
            raise InvalidLocationError("test")

        with pytest.raises(DomainError):
            raise InvalidPhoneNumberError("test")

        with pytest.raises(DomainError):
            raise InvalidItemCategoryError("test")

        with pytest.raises(DomainError):
            raise ItemNotFoundError("test")

        with pytest.raises(DomainError):
            raise ItemAlreadyRecoveredError("test")
