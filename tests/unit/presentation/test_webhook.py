"""Tests for WhatsApp webhook endpoints."""

import hashlib
import hmac
import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from src.presentation.api.dependencies import get_message_processor


def create_webhook_payload(
    phone_number: str, message_text: str
) -> dict[str, list[object]]:
    """Create a test webhook payload.

    Args:
        phone_number: Phone number to use in payload
        message_text: Message text to use in payload

    Returns:
        Webhook payload dictionary
    """
    return {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "from": phone_number,
                                    "id": "msg_123",
                                    "timestamp": "1234567890",
                                    "type": "text",
                                    "text": {"body": message_text},
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }


def sign_payload(
    payload: dict[str, object], app_secret: str = "test_app_secret"
) -> str:
    """Sign a webhook payload.

    Args:
        payload: Payload to sign
        app_secret: App secret to use for signing

    Returns:
        Signature header value (sha256=...)
    """
    payload_str = json.dumps(payload, separators=(",", ":"))
    signature = hmac.new(
        app_secret.encode("utf-8"),
        payload_str.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"sha256={signature}"


@pytest.fixture
def mock_message_processor() -> MagicMock:
    """Create a mock message processor."""
    processor = MagicMock()
    processor.process_message = AsyncMock(
        return_value={"reply": "test reply", "state": "idle"}
    )
    return processor


@pytest.fixture
def client_with_mock_processor(
    client: TestClient, mock_message_processor: MagicMock
) -> TestClient:
    """Override the message processor and IP rate limiter dependencies with mocks."""
    from src.presentation.api.app import app
    from src.presentation.api.dependencies import get_ip_rate_limiter

    # Mock message processor
    app.dependency_overrides[get_message_processor] = lambda: mock_message_processor

    # Mock IP rate limiter to always allow requests
    mock_ip_rate_limiter = MagicMock()
    mock_ip_rate_limiter.check_rate_limit = AsyncMock(return_value=None)
    app.dependency_overrides[get_ip_rate_limiter] = lambda: mock_ip_rate_limiter

    yield client
    app.dependency_overrides.clear()


@pytest.mark.unit
class TestWebhookVerification:
    """Test GET /v1/webhook verification endpoint."""

    def test_successful_verification(self, client: TestClient) -> None:
        """Test successful webhook verification."""
        # Arrange
        mode = "subscribe"
        verify_token = "test_verify_token"
        challenge = "test_challenge_1234"

        # Act
        response = client.get(
            "/v1/webhook",
            params={
                "hub.mode": mode,
                "hub.verify_token": verify_token,
                "hub.challenge": challenge,
            },
        )

        # Assert
        assert response.status_code == 200
        assert response.text == challenge

    def test_invalid_mode(self, client: TestClient) -> None:
        """Test verification fails with invalid mode."""
        # Arrange
        mode = "invalid"
        verify_token = "test_verify_token"
        challenge = "test_challenge"

        # Act
        response = client.get(
            "/v1/webhook",
            params={
                "hub.mode": mode,
                "hub.verify_token": verify_token,
                "hub.challenge": challenge,
            },
        )

        # Assert
        assert response.status_code == 403
        assert "Invalid mode" in response.json()["detail"]

    def test_invalid_verify_token(self, client: TestClient) -> None:
        """Test verification fails with invalid token."""
        # Arrange
        mode = "subscribe"
        verify_token = "wrong_token"
        challenge = "test_challenge"

        # Act
        response = client.get(
            "/v1/webhook",
            params={
                "hub.mode": mode,
                "hub.verify_token": verify_token,
                "hub.challenge": challenge,
            },
        )

        # Assert
        assert response.status_code == 403
        assert "Invalid verify token" in response.json()["detail"]


@pytest.mark.unit
class TestWebhookMessages:
    """Test POST /v1/webhook message endpoint."""

    def test_successful_message_receipt(
        self, client_with_mock_processor: TestClient
    ) -> None:
        """Test successful message receipt with valid signature."""
        # Arrange
        app_secret = "test_app_secret"
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "1234567890",
                                        "id": "msg_123",
                                        "timestamp": "1234567890",
                                        "type": "text",
                                        "text": {"body": "Hello"},
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }
        # Use compact JSON format (no spaces) to match FastAPI serialization
        payload_str = json.dumps(payload, separators=(",", ":"))

        # Generate valid signature
        signature = hmac.new(
            app_secret.encode("utf-8"),
            payload_str.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        # Act
        response = client_with_mock_processor.post(
            "/v1/webhook",
            json=payload,
            headers={"X-Hub-Signature-256": f"sha256={signature}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["messages_received"] == 1
        assert data["processed"] == 1
        assert data["failed"] == 0

    def test_invalid_signature(self, client_with_mock_processor: TestClient) -> None:
        """Test message receipt fails with invalid signature."""
        # Arrange
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "1234567890",
                                        "id": "msg_123",
                                        "timestamp": "1234567890",
                                        "type": "text",
                                        "text": {"body": "Hello"},
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }

        # Act - use invalid signature
        response = client_with_mock_processor.post(
            "/v1/webhook",
            json=payload,
            headers={"X-Hub-Signature-256": "sha256=invalid_signature"},
        )

        # Assert
        assert response.status_code == 403
        assert "Invalid signature" in response.json()["detail"]

    def test_empty_payload(self, client_with_mock_processor: TestClient) -> None:
        """Test handling of empty payload."""
        # Arrange
        app_secret = "test_app_secret"
        payload: dict[str, list[object]] = {"entry": []}
        payload_str = json.dumps(payload, separators=(",", ":"))

        # Generate valid signature
        signature = hmac.new(
            app_secret.encode("utf-8"),
            payload_str.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        # Act
        response = client_with_mock_processor.post(
            "/v1/webhook",
            json=payload,
            headers={"X-Hub-Signature-256": f"sha256={signature}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["messages_received"] == 0
        assert data["processed"] == 0
        assert data["failed"] == 0

    def test_multiple_messages(self, client_with_mock_processor: TestClient) -> None:
        """Test handling of multiple messages in one payload."""
        # Arrange
        app_secret = "test_app_secret"
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "1234567890",
                                        "id": "msg_1",
                                        "timestamp": "1234567890",
                                        "type": "text",
                                        "text": {"body": "Hello"},
                                    },
                                    {
                                        "from": "0987654321",
                                        "id": "msg_2",
                                        "timestamp": "1234567891",
                                        "type": "text",
                                        "text": {"body": "Hi there"},
                                    },
                                ]
                            }
                        }
                    ]
                }
            ]
        }
        payload_str = json.dumps(payload, separators=(",", ":"))

        # Generate valid signature
        signature = hmac.new(
            app_secret.encode("utf-8"),
            payload_str.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        # Act
        response = client_with_mock_processor.post(
            "/v1/webhook",
            json=payload,
            headers={"X-Hub-Signature-256": f"sha256={signature}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["messages_received"] == 2
        assert data["processed"] == 2
        assert data["failed"] == 0

    def test_media_message(self, client_with_mock_processor: TestClient) -> None:
        """Test handling of media message."""
        # Arrange
        app_secret = "test_app_secret"
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "1234567890",
                                        "id": "msg_media",
                                        "timestamp": "1234567890",
                                        "type": "image",
                                        "image": {
                                            "id": "media_123",
                                            "mime_type": "image/jpeg",
                                        },
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }
        payload_str = json.dumps(payload, separators=(",", ":"))

        # Generate valid signature
        signature = hmac.new(
            app_secret.encode("utf-8"),
            payload_str.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        # Act
        response = client_with_mock_processor.post(
            "/v1/webhook",
            json=payload,
            headers={"X-Hub-Signature-256": f"sha256={signature}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["messages_received"] == 1
        # Media messages have no text, so they won't be processed
        assert data["processed"] == 0
        assert data["failed"] == 1

    def test_message_processing_error_handling(
        self, client: TestClient, mock_message_processor: MagicMock
    ) -> None:
        """Test that message processing errors are handled gracefully."""
        # Arrange
        from src.presentation.api.app import app

        # Create a processor that raises an exception
        failing_processor = MagicMock()
        failing_processor.process_message = AsyncMock(
            side_effect=Exception("Processing failed")
        )

        app.dependency_overrides[get_message_processor] = lambda: failing_processor

        try:
            app_secret = "test_app_secret"
            payload = {
                "entry": [
                    {
                        "changes": [
                            {
                                "value": {
                                    "messages": [
                                        {
                                            "from": "1234567890",
                                            "id": "msg_123",
                                            "timestamp": "1234567890",
                                            "type": "text",
                                            "text": {"body": "Hello"},
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                ]
            }
            payload_str = json.dumps(payload, separators=(",", ":"))

            signature = hmac.new(
                app_secret.encode("utf-8"),
                payload_str.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()

            # Act
            response = client.post(
                "/v1/webhook",
                json=payload,
                headers={"X-Hub-Signature-256": f"sha256={signature}"},
            )

            # Assert
            assert response.status_code == 200  # Still returns 200
            data = response.json()
            assert data["status"] == "success"
            assert data["messages_received"] == 1
            assert data["processed"] == 0  # Failed to process
            assert data["failed"] == 1  # One failure

        finally:
            app.dependency_overrides.clear()

    def test_missing_signature_header(
        self, client_with_mock_processor: TestClient
    ) -> None:
        """Test that missing signature header is handled."""
        # Arrange
        payload: dict[str, list[object]] = {"entry": []}

        # Act - no signature header
        response = client_with_mock_processor.post("/v1/webhook", json=payload)

        # Assert
        assert (
            response.status_code == 422
        )  # FastAPI validation error for missing header


@pytest.mark.unit
class TestWebhookIPRateLimiting:
    """Test IP-based rate limiting for webhook endpoints."""

    @pytest.mark.asyncio
    async def test_webhook_allows_requests_within_ip_rate_limit(
        self, client_with_mock_processor: TestClient
    ) -> None:
        """Test that webhook POST requests within IP rate limit are allowed."""
        # Arrange
        payload = create_webhook_payload("1234567890", "test message")
        signature = sign_payload(payload)
        headers = {"X-Hub-Signature-256": signature}

        # Act - Make request from specific IP
        response = client_with_mock_processor.post(
            "/v1/webhook", json=payload, headers=headers
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["status"] == "success"

    def test_webhook_blocks_requests_exceeding_ip_rate_limit(
        self, client: TestClient
    ) -> None:
        """Test that webhook POST requests exceeding IP rate limit are blocked."""
        # Arrange
        from unittest.mock import AsyncMock, MagicMock

        from src.infrastructure.cache.rate_limiter import RateLimitExceeded
        from src.presentation.api.app import app
        from src.presentation.api.dependencies import (
            get_ip_rate_limiter,
            get_message_processor,
        )

        payload = create_webhook_payload("1234567890", "test message")
        signature = sign_payload(payload)
        headers = {"X-Hub-Signature-256": signature}

        # Mock message processor
        mock_processor = MagicMock()
        mock_processor.process_message = AsyncMock(
            return_value={"reply": "test", "state": "idle"}
        )
        app.dependency_overrides[get_message_processor] = lambda: mock_processor

        # Mock the IP rate limiter to raise RateLimitExceeded
        mock_rate_limiter = MagicMock()
        mock_rate_limiter.check_rate_limit = AsyncMock(
            side_effect=RateLimitExceeded("Rate limit exceeded", retry_after=60)
        )
        app.dependency_overrides[get_ip_rate_limiter] = lambda: mock_rate_limiter

        # Act
        response = client.post("/v1/webhook", json=payload, headers=headers)

        # Assert
        assert response.status_code == 429
        assert "rate limit" in response.json()["detail"].lower()
        assert "retry-after" in response.headers
        assert response.headers["retry-after"] == "60"

        # Cleanup
        app.dependency_overrides.clear()

    def test_webhook_get_not_affected_by_post_ip_rate_limit(
        self, client: TestClient
    ) -> None:
        """Test that webhook GET (verify) is not affected by POST rate limiting."""
        # Arrange - GET request for webhook verification
        params = {
            "hub.mode": "subscribe",
            "hub.verify_token": "test_verify_token",
            "hub.challenge": "test_challenge",
        }

        # Act - Make GET request (should not be rate limited by IP limiter)
        response = client.get("/v1/webhook", params=params)

        # Assert - Should work (GET endpoint doesn't use IP rate limiter)
        assert response.status_code == 200
        assert response.text == "test_challenge"

    def test_webhook_different_ips_have_separate_rate_limits(
        self, client: TestClient
    ) -> None:
        """Test that different IP addresses have independent rate limits."""
        from unittest.mock import AsyncMock, MagicMock

        from src.presentation.api.app import app
        from src.presentation.api.dependencies import (
            get_ip_rate_limiter,
            get_message_processor,
        )

        # Arrange
        payload = create_webhook_payload("1234567890", "test message")
        signature = sign_payload(payload)
        headers = {"X-Hub-Signature-256": signature}

        # Mock dependencies - both processor and rate limiter
        mock_processor = MagicMock()
        mock_processor.process_message = AsyncMock(
            return_value={"reply": "test", "state": "idle"}
        )
        app.dependency_overrides[get_message_processor] = lambda: mock_processor

        # Mock rate limiter to always allow requests (simulating separate IP limits)
        mock_rate_limiter = MagicMock()
        mock_rate_limiter.check_rate_limit = AsyncMock(return_value=None)
        app.dependency_overrides[get_ip_rate_limiter] = lambda: mock_rate_limiter

        # Act - Make requests from different IPs (via X-Forwarded-For)
        # These should both succeed as they use different IP limits
        response1 = client.post(
            "/v1/webhook",
            json=payload,
            headers={**headers, "X-Forwarded-For": "192.168.1.1"},
        )
        response2 = client.post(
            "/v1/webhook",
            json=payload,
            headers={**headers, "X-Forwarded-For": "192.168.1.2"},
        )

        # Assert - Both should succeed (separate limits per IP)
        assert response1.status_code == 200
        assert response2.status_code == 200

        # Verify rate limiter was called for both IPs
        assert mock_rate_limiter.check_rate_limit.call_count == 2
        mock_rate_limiter.check_rate_limit.assert_any_call("192.168.1.1")
        mock_rate_limiter.check_rate_limit.assert_any_call("192.168.1.2")

        # Cleanup
        app.dependency_overrides.clear()

    def test_webhook_rate_limit_error_includes_retry_after(
        self, client: TestClient
    ) -> None:
        """Test that rate limit error response includes Retry-After header."""
        # Arrange
        from unittest.mock import AsyncMock, MagicMock

        from src.infrastructure.cache.rate_limiter import RateLimitExceeded
        from src.presentation.api.app import app
        from src.presentation.api.dependencies import (
            get_ip_rate_limiter,
            get_message_processor,
        )

        payload = create_webhook_payload("1234567890", "test message")
        signature = sign_payload(payload)
        headers = {"X-Hub-Signature-256": signature}

        # Mock dependencies
        mock_processor = MagicMock()
        mock_processor.process_message = AsyncMock(
            return_value={"reply": "test", "state": "idle"}
        )
        app.dependency_overrides[get_message_processor] = lambda: mock_processor

        mock_rate_limiter = MagicMock()
        mock_rate_limiter.check_rate_limit = AsyncMock(
            side_effect=RateLimitExceeded("Rate limit exceeded", retry_after=120)
        )
        app.dependency_overrides[get_ip_rate_limiter] = lambda: mock_rate_limiter

        # Act
        response = client.post("/v1/webhook", json=payload, headers=headers)

        # Assert
        assert response.status_code == 429
        assert "retry after 120 seconds" in response.json()["detail"].lower()
        assert response.headers["retry-after"] == "120"

        # Cleanup
        app.dependency_overrides.clear()

    def test_get_client_ip_fallback_to_unknown(self) -> None:
        """Test that get_client_ip returns 'unknown' when no client info available."""
        from unittest.mock import MagicMock

        from src.presentation.api.v1.webhook import get_client_ip

        # Arrange - Mock request with no X-Forwarded-For and no client
        mock_request = MagicMock()
        mock_request.headers.get.return_value = None
        mock_request.client = None

        # Act
        result = get_client_ip(mock_request)

        # Assert
        assert result == "unknown"


@pytest.mark.unit
class TestWebhookLocationMessages:
    """Test location message handling in webhook endpoint."""

    def test_location_message_processing(
        self, client_with_mock_processor: TestClient
    ) -> None:
        """Test that location messages are processed correctly."""
        # Arrange
        app_secret = "test_app_secret"
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "1234567890",
                                        "id": "msg_location",
                                        "timestamp": "1234567890",
                                        "type": "location",
                                        "location": {
                                            "latitude": 51.5074,
                                            "longitude": -0.1278,
                                            "name": "London Eye",
                                            "address": "County Hall, London",
                                        },
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }
        payload_str = json.dumps(payload, separators=(",", ":"))

        # Generate valid signature
        signature = hmac.new(
            app_secret.encode("utf-8"),
            payload_str.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        # Act
        response = client_with_mock_processor.post(
            "/v1/webhook",
            json=payload,
            headers={"X-Hub-Signature-256": f"sha256={signature}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["messages_received"] == 1
        assert data["processed"] == 1
        assert data["failed"] == 0

    def test_location_message_without_optional_fields(
        self, client_with_mock_processor: TestClient
    ) -> None:
        """Test location message without name and address."""
        # Arrange
        app_secret = "test_app_secret"
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "1234567890",
                                        "id": "msg_location",
                                        "timestamp": "1234567890",
                                        "type": "location",
                                        "location": {
                                            "latitude": 51.5074,
                                            "longitude": -0.1278,
                                        },
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }
        payload_str = json.dumps(payload, separators=(",", ":"))

        signature = hmac.new(
            app_secret.encode("utf-8"),
            payload_str.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        # Act
        response = client_with_mock_processor.post(
            "/v1/webhook",
            json=payload,
            headers={"X-Hub-Signature-256": f"sha256={signature}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["messages_received"] == 1
        assert data["processed"] == 1
        assert data["failed"] == 0

    def test_location_message_without_coordinates_is_skipped(
        self, client_with_mock_processor: TestClient
    ) -> None:
        """Test that location message without coordinates is skipped."""
        # Arrange
        app_secret = "test_app_secret"
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "1234567890",
                                        "id": "msg_location",
                                        "timestamp": "1234567890",
                                        "type": "location",
                                        "location": {
                                            "name": "Some place",
                                            # Missing latitude and longitude
                                        },
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }
        payload_str = json.dumps(payload, separators=(",", ":"))

        signature = hmac.new(
            app_secret.encode("utf-8"),
            payload_str.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        # Act
        response = client_with_mock_processor.post(
            "/v1/webhook",
            json=payload,
            headers={"X-Hub-Signature-256": f"sha256={signature}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["messages_received"] == 1
        assert data["processed"] == 0
        assert data["failed"] == 1  # Skipped due to missing coordinates

    def test_message_without_phone_number_is_skipped(
        self, client_with_mock_processor: TestClient
    ) -> None:
        """Test that message without phone number is skipped."""
        # Arrange
        app_secret = "test_app_secret"
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        # Missing "from" field
                                        "id": "msg_123",
                                        "timestamp": "1234567890",
                                        "type": "text",
                                        "text": {"body": "Hello"},
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }
        payload_str = json.dumps(payload, separators=(",", ":"))

        signature = hmac.new(
            app_secret.encode("utf-8"),
            payload_str.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        # Act
        response = client_with_mock_processor.post(
            "/v1/webhook",
            json=payload,
            headers={"X-Hub-Signature-256": f"sha256={signature}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        # Message won't be parsed due to missing required field
        assert data["messages_received"] == 0
        assert data["processed"] == 0
        assert data["failed"] == 0

    def test_mixed_text_and_location_messages(
        self, client_with_mock_processor: TestClient
    ) -> None:
        """Test handling of both text and location messages in one payload."""
        # Arrange
        app_secret = "test_app_secret"
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "1234567890",
                                        "id": "msg_text",
                                        "timestamp": "1234567890",
                                        "type": "text",
                                        "text": {"body": "Hello"},
                                    },
                                    {
                                        "from": "1234567890",
                                        "id": "msg_location",
                                        "timestamp": "1234567891",
                                        "type": "location",
                                        "location": {
                                            "latitude": 51.5,
                                            "longitude": -0.1,
                                        },
                                    },
                                ]
                            }
                        }
                    ]
                }
            ]
        }
        payload_str = json.dumps(payload, separators=(",", ":"))

        signature = hmac.new(
            app_secret.encode("utf-8"),
            payload_str.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        # Act
        response = client_with_mock_processor.post(
            "/v1/webhook",
            json=payload,
            headers={"X-Hub-Signature-256": f"sha256={signature}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["messages_received"] == 2
        assert data["processed"] == 2
        assert data["failed"] == 0

    def test_debug_logging_in_dev_environment(
        self, client_with_mock_processor: TestClient, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that debug logging is enabled in dev/test environment."""
        import logging

        # Arrange
        app_secret = "test_app_secret"
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "1234567890",
                                        "id": "msg_test",
                                        "timestamp": "1234567890",
                                        "type": "text",
                                        "text": {"body": "Test message"},
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }
        payload_str = json.dumps(payload, separators=(",", ":"))

        signature = hmac.new(
            app_secret.encode("utf-8"),
            payload_str.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        # Act - capture logs at DEBUG level
        with caplog.at_level(logging.DEBUG):
            response = client_with_mock_processor.post(
                "/v1/webhook",
                json=payload,
                headers={"X-Hub-Signature-256": f"sha256={signature}"},
            )

        # Assert
        assert response.status_code == 200

        # Check that debug logs were created (environment is "test")
        debug_messages = [
            record.message
            for record in caplog.records
            if record.levelno == logging.DEBUG
        ]
        assert any("Received webhook payload" in msg for msg in debug_messages)
        assert any("Processing message" in msg for msg in debug_messages)

    # NOTE: Branch coverage gaps 151->158, 173->186, 187-192 are intentionally not tested:
    # - 151->158 & 173->186: FALSE branch for production environment (no debug logging)
    #   Testing this would require reloading modules mid-test which is unreliable
    # - 187-192: Defensive code for missing phone_number that can never be reached
    #   because webhook_handler validates "from" field before messages reach this code


@pytest.mark.unit
class TestPhoneNumberRedaction:
    """Test phone number redaction for logging security."""

    def test_redact_phone_number_with_full_number(self) -> None:
        """Test redacting a full phone number."""
        from src.presentation.api.v1.webhook import redact_phone_number

        # Arrange
        phone = "1234567890"

        # Act
        result = redact_phone_number(phone)

        # Assert
        assert result == "***7890"
        assert "1234" not in result

    def test_redact_phone_number_with_short_number(self) -> None:
        """Test redacting a short phone number (4 digits or less)."""
        from src.presentation.api.v1.webhook import redact_phone_number

        # Arrange
        phone = "1234"

        # Act
        result = redact_phone_number(phone)

        # Assert
        assert result == "***"

    def test_redact_phone_number_with_empty_string(self) -> None:
        """Test redacting an empty phone number."""
        from src.presentation.api.v1.webhook import redact_phone_number

        # Arrange
        phone = ""

        # Act
        result = redact_phone_number(phone)

        # Assert
        assert result == "***"

    def test_redact_message_data_with_phone(self) -> None:
        """Test redacting phone number from message data."""
        from src.presentation.api.v1.webhook import redact_message_data

        # Arrange
        msg = {
            "from": "1234567890",
            "text": "Hello",
            "type": "text",
        }

        # Act
        result = redact_message_data(msg)

        # Assert
        assert result["from"] == "***7890"
        assert result["text"] == "Hello"
        assert result["type"] == "text"
        # Ensure original is not modified
        assert msg["from"] == "1234567890"

    def test_redact_message_data_without_phone(self) -> None:
        """Test redacting message data without phone number."""
        from src.presentation.api.v1.webhook import redact_message_data

        # Arrange
        msg = {
            "text": "Hello",
            "type": "text",
        }

        # Act
        result = redact_message_data(msg)

        # Assert
        assert "from" not in result
        assert result["text"] == "Hello"
        assert result["type"] == "text"

    def test_redact_payload_phone_numbers(self) -> None:
        """Test redacting phone numbers from full webhook payload."""
        from src.presentation.api.v1.webhook import _redact_payload_phone_numbers

        # Arrange - WhatsApp webhook structure
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "1234567890",
                                        "text": {"body": "Hello"},
                                        "type": "text",
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }

        # Act
        result = _redact_payload_phone_numbers(payload)

        # Assert
        assert (
            result["entry"][0]["changes"][0]["value"]["messages"][0]["from"]
            == "***7890"
        )
        # Ensure original is not modified
        assert (
            payload["entry"][0]["changes"][0]["value"]["messages"][0]["from"]
            == "1234567890"
        )

    def test_redact_payload_phone_numbers_empty_payload(self) -> None:
        """Test redacting phone numbers from empty payload."""
        from src.presentation.api.v1.webhook import _redact_payload_phone_numbers

        # Arrange
        payload: dict[str, object] = {}

        # Act
        result = _redact_payload_phone_numbers(payload)

        # Assert
        assert result == {}

    def test_redact_payload_phone_numbers_malformed_structure(self) -> None:
        """Test redacting phone numbers handles malformed structures."""
        from src.presentation.api.v1.webhook import _redact_payload_phone_numbers

        # Arrange - malformed webhook structure
        payload = {
            "entry": "not_a_list",  # Should be list
        }

        # Act
        result = _redact_payload_phone_numbers(payload)

        # Assert - Should not crash
        assert result == {"entry": "not_a_list"}

    def test_redact_payload_handles_json_serialization_error(self) -> None:
        """Test that redaction falls back gracefully if JSON serialization fails."""
        from unittest.mock import patch

        from src.presentation.api.v1.webhook import _redact_payload_phone_numbers

        # Arrange - payload with phone number
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "1234567890",
                                        "type": "text",
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }

        # Mock json.dumps to raise TypeError to trigger fallback path
        with patch("json.dumps", side_effect=TypeError("Mock serialization error")):
            # Act
            result = _redact_payload_phone_numbers(payload)

        # Assert - Should still redact phone and return result (fallback path)
        assert (
            result["entry"][0]["changes"][0]["value"]["messages"][0]["from"]
            == "***7890"
        )
