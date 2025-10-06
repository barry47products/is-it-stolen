"""Unit tests for Sentry error tracking integration."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.infrastructure.config.settings import Settings
from src.infrastructure.monitoring.sentry import (
    capture_exception,
    capture_message,
    init_sentry,
    set_context,
    set_tag,
    set_user,
)


class TestSentryInitialization:
    """Test Sentry SDK initialization."""

    @patch("src.infrastructure.monitoring.sentry.sentry_sdk.init")
    def test_initializes_sentry_with_dsn(self, mock_init: MagicMock) -> None:
        """Test that Sentry initializes when DSN is provided."""
        # Arrange
        settings = Settings(
            database_url="postgresql://user:pass@localhost/test",
            sentry_dsn="https://key@sentry.io/project",
            sentry_environment="test",
            sentry_release="1.0.0",
            sentry_traces_sample_rate=0.5,
            sentry_profiles_sample_rate=0.3,
        )

        # Act
        init_sentry(settings)

        # Assert
        mock_init.assert_called_once()
        call_kwargs = mock_init.call_args.kwargs
        assert call_kwargs["dsn"] == "https://key@sentry.io/project"
        assert call_kwargs["environment"] == "test"
        assert call_kwargs["release"] == "1.0.0"
        assert call_kwargs["traces_sample_rate"] == 0.5
        assert call_kwargs["send_default_pii"] is False
        assert len(call_kwargs["integrations"]) == 3  # FastAPI, Redis, Logging

    @patch("src.infrastructure.monitoring.sentry.sentry_sdk.init")
    def test_skips_initialization_without_dsn(self, mock_init: MagicMock) -> None:
        """Test that Sentry does not initialize when DSN is empty."""
        # Arrange
        settings = Settings(
            database_url="postgresql://user:pass@localhost/test",
            sentry_dsn="",
        )

        # Act
        init_sentry(settings)

        # Assert
        mock_init.assert_not_called()

    @patch("src.infrastructure.monitoring.sentry.sentry_sdk.init")
    def test_uses_unknown_release_when_not_provided(self, mock_init: MagicMock) -> None:
        """Test that 'unknown' is used when release is not provided."""
        # Arrange
        settings = Settings(
            database_url="postgresql://user:pass@localhost/test",
            sentry_dsn="https://key@sentry.io/project",
            sentry_release="",
        )

        # Act
        init_sentry(settings)

        # Assert
        call_kwargs = mock_init.call_args.kwargs
        assert call_kwargs["release"] == "unknown"

    @patch("src.infrastructure.monitoring.sentry.sentry_sdk.init")
    def test_defaults_to_development_environment(self, mock_init: MagicMock) -> None:
        """Test that environment defaults to 'development' when not set."""
        # Arrange
        settings = Settings(
            database_url="postgresql://user:pass@localhost/test",
            sentry_dsn="https://key@sentry.io/project",
            sentry_environment="",  # Empty string
        )

        # Act
        init_sentry(settings)

        # Assert
        call_kwargs = mock_init.call_args.kwargs
        assert call_kwargs["environment"] == "development"


class TestBeforeSend:
    """Test before_send callback for data filtering."""

    @patch("src.infrastructure.monitoring.sentry.sentry_sdk.init")
    def test_scrubs_sensitive_headers(self, mock_init: MagicMock) -> None:
        """Test that sensitive headers are scrubbed from error reports."""
        # Arrange
        settings = Settings(
            database_url="postgresql://user:pass@localhost/test",
            sentry_dsn="https://key@sentry.io/project",
        )
        init_sentry(settings)

        # Get the before_send callback
        before_send = mock_init.call_args.kwargs["before_send"]

        event = {
            "request": {
                "headers": {
                    "Authorization": "Bearer secret-token",
                    "Content-Type": "application/json",
                    "X-Api-Key": "secret-key",
                }
            }
        }

        # Act
        result = before_send(event, {})

        # Assert
        assert result is not None
        assert result["request"]["headers"]["Authorization"] == "[Filtered]"
        assert result["request"]["headers"]["Content-Type"] == "application/json"
        assert result["request"]["headers"]["X-Api-Key"] == "[Filtered]"

    @patch("src.infrastructure.monitoring.sentry.sentry_sdk.init")
    def test_scrubs_sensitive_body_fields(self, mock_init: MagicMock) -> None:
        """Test that sensitive body fields are scrubbed."""
        # Arrange
        settings = Settings(
            database_url="postgresql://user:pass@localhost/test",
            sentry_dsn="https://key@sentry.io/project",
        )
        init_sentry(settings)

        before_send = mock_init.call_args.kwargs["before_send"]

        event = {
            "request": {
                "data": {
                    "username": "testuser",
                    "password": "secret123",
                    "access_token": "token123",
                }
            }
        }

        # Act
        result = before_send(event, {})

        # Assert
        assert result is not None
        assert result["request"]["data"]["username"] == "testuser"
        assert result["request"]["data"]["password"] == "[Filtered]"
        assert result["request"]["data"]["access_token"] == "[Filtered]"

    @patch("src.infrastructure.monitoring.sentry.sentry_sdk.init")
    def test_scrubs_nested_sensitive_data(self, mock_init: MagicMock) -> None:
        """Test that nested sensitive data is scrubbed."""
        # Arrange
        settings = Settings(
            database_url="postgresql://user:pass@localhost/test",
            sentry_dsn="https://key@sentry.io/project",
        )
        init_sentry(settings)

        before_send = mock_init.call_args.kwargs["before_send"]

        event = {
            "extra": {
                "user_data": {
                    "name": "John Doe",
                    "credentials": {
                        "api_key": "secret-key",
                        "secret": "secret-value",
                    },
                }
            }
        }

        # Act
        result = before_send(event, {})

        # Assert
        assert result is not None
        assert result["extra"]["user_data"]["name"] == "John Doe"
        assert result["extra"]["user_data"]["credentials"]["api_key"] == "[Filtered]"
        assert result["extra"]["user_data"]["credentials"]["secret"] == "[Filtered]"


class TestSentryHelpers:
    """Test Sentry helper functions."""

    @patch("src.infrastructure.monitoring.sentry.sentry_sdk.capture_exception")
    def test_capture_exception_without_context(self, mock_capture: MagicMock) -> None:
        """Test capturing exception without additional context."""
        # Arrange
        error = ValueError("Test error")

        # Act
        capture_exception(error)

        # Assert
        mock_capture.assert_called_once_with(error)

    @patch("src.infrastructure.monitoring.sentry.sentry_sdk.capture_exception")
    @patch("src.infrastructure.monitoring.sentry.sentry_sdk.isolation_scope")
    def test_capture_exception_with_context(
        self, mock_isolation_scope: MagicMock, mock_capture: MagicMock
    ) -> None:
        """Test capturing exception with additional context."""
        # Arrange
        error = ValueError("Test error")
        mock_scope = MagicMock()
        mock_isolation_scope.return_value.__enter__ = MagicMock(return_value=mock_scope)
        mock_isolation_scope.return_value.__exit__ = MagicMock(return_value=False)

        # Act
        capture_exception(error, user_id="123", action="test")

        # Assert
        mock_scope.set_context.assert_any_call("user_id", "123")
        mock_scope.set_context.assert_any_call("action", "test")
        mock_capture.assert_called_once_with(error)

    @patch("src.infrastructure.monitoring.sentry.sentry_sdk.capture_message")
    def test_capture_message_info_level(self, mock_capture: MagicMock) -> None:
        """Test capturing info message."""
        # Arrange
        message = "Test info message"

        # Act
        capture_message(message, level="info")

        # Assert
        mock_capture.assert_called_once_with(message, level="info")

    @patch("src.infrastructure.monitoring.sentry.sentry_sdk.capture_message")
    def test_capture_message_warning_level(self, mock_capture: MagicMock) -> None:
        """Test capturing warning message."""
        # Arrange
        message = "Test warning message"

        # Act
        capture_message(message, level="warning")

        # Assert
        mock_capture.assert_called_once_with(message, level="warning")

    @patch("src.infrastructure.monitoring.sentry.sentry_sdk.set_user")
    def test_set_user_context(self, mock_set_user: MagicMock) -> None:
        """Test setting user context."""
        # Arrange
        user_id = "123"
        user_phone = "+1234567890"

        # Act
        set_user(user_id, phone=user_phone)

        # Assert
        mock_set_user.assert_called_once_with({"id": "123", "phone": "+1234567890"})

    @patch("src.infrastructure.monitoring.sentry.sentry_sdk.capture_message")
    @patch("src.infrastructure.monitoring.sentry.sentry_sdk.isolation_scope")
    def test_capture_message_with_context(
        self, mock_isolation_scope: MagicMock, mock_capture: MagicMock
    ) -> None:
        """Test capturing message with additional context."""
        # Arrange
        message = "Test message with context"
        mock_scope = MagicMock()
        mock_isolation_scope.return_value.__enter__ = MagicMock(return_value=mock_scope)
        mock_isolation_scope.return_value.__exit__ = MagicMock(return_value=False)

        # Act
        capture_message(message, level="warning", user_id="123")

        # Assert
        mock_scope.set_context.assert_called_once_with("user_id", "123")
        mock_capture.assert_called_once_with(message, level="warning")

    @patch("src.infrastructure.monitoring.sentry.sentry_sdk.set_tag")
    def test_set_tag(self, mock_set_tag: MagicMock) -> None:
        """Test setting a tag for error grouping."""
        # Act
        set_tag("category", "bicycle")

        # Assert
        mock_set_tag.assert_called_once_with("category", "bicycle")

    @patch("src.infrastructure.monitoring.sentry.sentry_sdk.set_context")
    def test_set_context(self, mock_set_context: MagicMock) -> None:
        """Test setting additional context."""
        # Arrange
        context_data = {"report_id": "123", "user_phone": "+1234567890"}

        # Act
        set_context("report_details", context_data)

        # Assert
        mock_set_context.assert_called_once_with("report_details", context_data)


class TestBeforeSendEdgeCases:
    """Test edge cases in before_send callback."""

    @patch("src.infrastructure.monitoring.sentry.sentry_sdk.init")
    def test_handles_event_without_request(self, mock_init: MagicMock) -> None:
        """Test that before_send handles events without request data."""
        # Arrange
        settings = Settings(
            database_url="postgresql://user:pass@localhost/test",
            sentry_dsn="https://key@sentry.io/project",
        )
        init_sentry(settings)
        before_send = mock_init.call_args.kwargs["before_send"]

        event = {"message": "Test error without request"}

        # Act
        result = before_send(event, {})

        # Assert
        assert result is not None
        assert result["message"] == "Test error without request"

    @patch("src.infrastructure.monitoring.sentry.sentry_sdk.init")
    def test_handles_non_dict_request_data(self, mock_init: MagicMock) -> None:
        """Test that before_send handles non-dict request data."""
        # Arrange
        settings = Settings(
            database_url="postgresql://user:pass@localhost/test",
            sentry_dsn="https://key@sentry.io/project",
        )
        init_sentry(settings)
        before_send = mock_init.call_args.kwargs["before_send"]

        event = {"request": {"data": "string data, not a dict"}}

        # Act
        result = before_send(event, {})

        # Assert
        assert result is not None
        assert result["request"]["data"] == "string data, not a dict"

    @patch("src.infrastructure.monitoring.sentry.sentry_sdk.init")
    def test_scrubs_list_of_dicts(self, mock_init: MagicMock) -> None:
        """Test that scrubbing works for lists containing dictionaries."""
        # Arrange
        settings = Settings(
            database_url="postgresql://user:pass@localhost/test",
            sentry_dsn="https://key@sentry.io/project",
        )
        init_sentry(settings)
        before_send = mock_init.call_args.kwargs["before_send"]

        event = {
            "extra": {
                "users": [
                    {"name": "John", "password": "secret1"},
                    {"name": "Jane", "api_key": "secret2"},
                ]
            }
        }

        # Act
        result = before_send(event, {})

        # Assert
        assert result is not None
        assert result["extra"]["users"][0]["name"] == "John"
        assert result["extra"]["users"][0]["password"] == "[Filtered]"
        assert result["extra"]["users"][1]["name"] == "Jane"
        assert result["extra"]["users"][1]["api_key"] == "[Filtered]"

    @patch("src.infrastructure.monitoring.sentry.sentry_sdk.init")
    def test_scrubs_query_string_parameters(self, mock_init: MagicMock) -> None:
        """Test that query string parameters are scrubbed."""
        # Arrange
        settings = Settings(
            database_url="postgresql://user:pass@localhost/test",
            sentry_dsn="https://key@sentry.io/project",
        )
        init_sentry(settings)
        before_send = mock_init.call_args.kwargs["before_send"]

        event = {"request": {"query_string": "user=john&api_key=secret123&page=1"}}

        # Act
        result = before_send(event, {})

        # Assert
        assert result is not None
        query = result["request"]["query_string"]
        assert "user=john" in query
        assert "api_key=[Filtered]" in query
        assert "page=1" in query

    @patch("src.infrastructure.monitoring.sentry.sentry_sdk.init")
    def test_handles_empty_query_string(self, mock_init: MagicMock) -> None:
        """Test that empty query strings are handled correctly."""
        # Arrange
        settings = Settings(
            database_url="postgresql://user:pass@localhost/test",
            sentry_dsn="https://key@sentry.io/project",
        )
        init_sentry(settings)
        before_send = mock_init.call_args.kwargs["before_send"]

        event = {"request": {"query_string": ""}}

        # Act
        result = before_send(event, {})

        # Assert
        assert result is not None
        assert result["request"]["query_string"] == ""

    @patch("src.infrastructure.monitoring.sentry.sentry_sdk.init")
    def test_handles_query_params_without_equals(self, mock_init: MagicMock) -> None:
        """Test that query params without = are preserved."""
        # Arrange
        settings = Settings(
            database_url="postgresql://user:pass@localhost/test",
            sentry_dsn="https://key@sentry.io/project",
        )
        init_sentry(settings)
        before_send = mock_init.call_args.kwargs["before_send"]

        event = {"request": {"query_string": "flag1&user=john&flag2"}}

        # Act
        result = before_send(event, {})

        # Assert
        assert result is not None
        query = result["request"]["query_string"]
        assert "flag1" in query
        assert "user=john" in query
        assert "flag2" in query

    @patch("src.infrastructure.monitoring.sentry.sentry_sdk.init")
    def test_scrubs_cookies(self, mock_init: MagicMock) -> None:
        """Test that cookies are scrubbed."""
        # Arrange
        settings = Settings(
            database_url="postgresql://user:pass@localhost/test",
            sentry_dsn="https://key@sentry.io/project",
        )
        init_sentry(settings)
        before_send = mock_init.call_args.kwargs["before_send"]

        event = {
            "request": {
                "cookies": {
                    "session_id": "abc123",
                    "user_pref": "dark_mode",
                }
            }
        }

        # Act
        result = before_send(event, {})

        # Assert
        assert result is not None
        assert result["request"]["cookies"]["session_id"] == "[Filtered]"
        assert result["request"]["cookies"]["user_pref"] == "dark_mode"

    @patch("src.infrastructure.monitoring.sentry.sentry_sdk.init")
    def test_scrubs_contexts(self, mock_init: MagicMock) -> None:
        """Test that contexts are scrubbed."""
        # Arrange
        settings = Settings(
            database_url="postgresql://user:pass@localhost/test",
            sentry_dsn="https://key@sentry.io/project",
        )
        init_sentry(settings)
        before_send = mock_init.call_args.kwargs["before_send"]

        event = {
            "contexts": {
                "user": {
                    "id": "123",
                    "access_token": "secret",
                }
            }
        }

        # Act
        result = before_send(event, {})

        # Assert
        assert result is not None
        assert result["contexts"]["user"]["id"] == "123"
        assert result["contexts"]["user"]["access_token"] == "[Filtered]"


class TestSentryPrivacy:
    """Test privacy-focused features of Sentry integration."""

    @patch("src.infrastructure.monitoring.sentry.sentry_sdk.init")
    def test_send_default_pii_is_false(self, mock_init: MagicMock) -> None:
        """Test that PII sending is disabled by default."""
        # Arrange
        settings = Settings(
            database_url="postgresql://user:pass@localhost/test",
            sentry_dsn="https://key@sentry.io/project",
        )

        # Act
        init_sentry(settings)

        # Assert
        call_kwargs = mock_init.call_args.kwargs
        assert call_kwargs["send_default_pii"] is False

    @patch("src.infrastructure.monitoring.sentry.sentry_sdk.init")
    def test_scrubs_common_password_fields(self, mock_init: MagicMock) -> None:
        """Test that common password field names are scrubbed."""
        # Arrange
        settings = Settings(
            database_url="postgresql://user:pass@localhost/test",
            sentry_dsn="https://key@sentry.io/project",
        )
        init_sentry(settings)

        before_send = mock_init.call_args.kwargs["before_send"]

        event = {
            "request": {
                "data": {
                    "password": "secret1",
                    "passwd": "secret2",
                    "pwd": "secret3",
                    "user_password": "secret4",
                }
            }
        }

        # Act
        result = before_send(event, {})

        # Assert
        assert result is not None
        data = result["request"]["data"]
        assert data["password"] == "[Filtered]"
        assert data["passwd"] == "[Filtered]"
        assert data["pwd"] == "[Filtered]"
        assert data["user_password"] == "[Filtered]"

    @patch("src.infrastructure.monitoring.sentry.sentry_sdk.init")
    def test_scrubs_token_variations(self, mock_init: MagicMock) -> None:
        """Test that various token field names are scrubbed."""
        # Arrange
        settings = Settings(
            database_url="postgresql://user:pass@localhost/test",
            sentry_dsn="https://key@sentry.io/project",
        )
        init_sentry(settings)

        before_send = mock_init.call_args.kwargs["before_send"]

        event = {
            "request": {
                "data": {
                    "access_token": "token1",
                    "refresh_token": "token2",
                    "api_token": "token3",
                    "bearer_token": "token4",
                }
            }
        }

        # Act
        result = before_send(event, {})

        # Assert
        assert result is not None
        data = result["request"]["data"]
        assert data["access_token"] == "[Filtered]"
        assert data["refresh_token"] == "[Filtered]"
        assert data["api_token"] == "[Filtered]"
        assert data["bearer_token"] == "[Filtered]"
