"""Unit tests for logging processors."""

from __future__ import annotations

from src.infrastructure.logging.processors import (
    add_hashed_phone,
    filter_sensitive_data,
    hash_phone_number,
)


class TestHashPhoneNumber:
    """Test phone number hashing for privacy."""

    def test_hashes_phone_number_consistently(self) -> None:
        """Test that same phone number always produces same hash."""
        # Arrange
        phone = "+447700900000"

        # Act
        hash1 = hash_phone_number(phone)
        hash2 = hash_phone_number(phone)

        # Assert
        assert hash1 == hash2
        assert len(hash1) == 8
        assert hash1.isalnum()

    def test_different_phones_produce_different_hashes(self) -> None:
        """Test that different phone numbers produce different hashes."""
        # Arrange
        phone1 = "+447700900000"
        phone2 = "+447700900001"

        # Act
        hash1 = hash_phone_number(phone1)
        hash2 = hash_phone_number(phone2)

        # Assert
        assert hash1 != hash2


class TestAddHashedPhone:
    """Test processor for adding hashed phone to log events."""

    def test_adds_hashed_phone_when_phone_present(self) -> None:
        """Test that phone is hashed and replaced with user_id_hash."""
        # Arrange
        event_dict = {
            "event": "User action",
            "phone": "+447700900000",
            "action": "report",
        }

        # Act
        result = add_hashed_phone(None, "", event_dict)

        # Assert
        assert "user_id_hash" in result
        assert "phone" not in result
        assert result["user_id_hash"] == hash_phone_number("+447700900000")
        assert result["action"] == "report"

    def test_does_nothing_when_phone_not_present(self) -> None:
        """Test that processor does nothing when phone is absent."""
        # Arrange
        event_dict = {"event": "System action", "action": "startup"}

        # Act
        result = add_hashed_phone(None, "", event_dict)

        # Assert
        assert "user_id_hash" not in result
        assert "phone" not in result
        assert result == event_dict

    def test_does_nothing_when_phone_is_empty(self) -> None:
        """Test that processor does nothing when phone is empty."""
        # Arrange
        event_dict = {"event": "System action", "phone": "", "action": "startup"}

        # Act
        result = add_hashed_phone(None, "", event_dict)

        # Assert
        assert "user_id_hash" not in result
        assert result["phone"] == ""


class TestFilterSensitiveData:
    """Test processor for filtering sensitive data from logs."""

    def test_filters_password_field(self) -> None:
        """Test that password fields are redacted."""
        # Arrange
        event_dict = {
            "event": "User login",
            "username": "user@example.com",
            "password": "secret123",
        }

        # Act
        result = filter_sensitive_data(None, "", event_dict)

        # Assert
        assert result["password"] == "[REDACTED]"
        assert result["username"] == "user@example.com"

    def test_filters_token_variations(self) -> None:
        """Test that various token field names are redacted."""
        # Arrange
        event_dict = {
            "access_token": "token1",
            "refresh_token": "token2",
            "api_token": "token3",
        }

        # Act
        result = filter_sensitive_data(None, "", event_dict)

        # Assert
        assert result["access_token"] == "[REDACTED]"
        assert result["refresh_token"] == "[REDACTED]"
        assert result["api_token"] == "[REDACTED]"

    def test_filters_api_key_variations(self) -> None:
        """Test that API key field variations are redacted."""
        # Arrange
        event_dict = {
            "api_key": "key1",
            "apiKey": "key2",
            "x_api_key": "key3",
        }

        # Act
        result = filter_sensitive_data(None, "", event_dict)

        # Assert
        assert result["api_key"] == "[REDACTED]"
        assert result["apiKey"] == "[REDACTED]"
        assert result["x_api_key"] == "[REDACTED]"

    def test_filters_nested_sensitive_data(self) -> None:
        """Test that nested sensitive data is redacted."""
        # Arrange
        event_dict = {
            "user": {
                "name": "John Doe",
                "credentials": {"password": "secret", "api_key": "key123"},
            }
        }

        # Act
        result = filter_sensitive_data(None, "", event_dict)

        # Assert
        assert result["user"]["name"] == "John Doe"
        assert result["user"]["credentials"]["password"] == "[REDACTED]"
        assert result["user"]["credentials"]["api_key"] == "[REDACTED]"

    def test_filters_sensitive_data_in_lists(self) -> None:
        """Test that sensitive data in lists is redacted."""
        # Arrange
        event_dict = {
            "users": [
                {"name": "John", "password": "secret1"},
                {"name": "Jane", "api_key": "key123"},
            ]
        }

        # Act
        result = filter_sensitive_data(None, "", event_dict)

        # Assert
        assert result["users"][0]["name"] == "John"
        assert result["users"][0]["password"] == "[REDACTED]"
        assert result["users"][1]["name"] == "Jane"
        assert result["users"][1]["api_key"] == "[REDACTED]"

    def test_preserves_non_sensitive_data(self) -> None:
        """Test that non-sensitive data is not modified."""
        # Arrange
        event_dict = {
            "event": "User action",
            "user_id": "123",
            "action": "report",
            "category": "bicycle",
            "metadata": {"count": 5, "timestamp": "2025-10-06"},
        }

        # Act
        result = filter_sensitive_data(None, "", event_dict)

        # Assert
        assert result == event_dict

    def test_filters_authorization_header(self) -> None:
        """Test that authorization headers are redacted."""
        # Arrange
        event_dict = {
            "headers": {"Authorization": "Bearer token123", "Content-Type": "json"}
        }

        # Act
        result = filter_sensitive_data(None, "", event_dict)

        # Assert
        assert result["headers"]["Authorization"] == "[REDACTED]"
        assert result["headers"]["Content-Type"] == "json"

    def test_filters_credit_card_fields(self) -> None:
        """Test that credit card related fields are redacted."""
        # Arrange
        event_dict = {
            "payment": {"credit_card": "1234567890123456", "cvv": "123", "amount": 100}
        }

        # Act
        result = filter_sensitive_data(None, "", event_dict)

        # Assert
        assert result["payment"]["credit_card"] == "[REDACTED]"
        assert result["payment"]["cvv"] == "[REDACTED]"
        assert result["payment"]["amount"] == 100
