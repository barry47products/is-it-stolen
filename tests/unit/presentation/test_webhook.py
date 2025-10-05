"""Tests for WhatsApp webhook endpoints."""

import hashlib
import hmac
import json

import pytest
from fastapi.testclient import TestClient


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

    def test_successful_message_receipt(self, client: TestClient) -> None:
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
        response = client.post(
            "/v1/webhook",
            json=payload,
            headers={"X-Hub-Signature-256": f"sha256={signature}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["messages_received"] == 1

    def test_invalid_signature(self, client: TestClient) -> None:
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
        response = client.post(
            "/v1/webhook",
            json=payload,
            headers={"X-Hub-Signature-256": "sha256=invalid_signature"},
        )

        # Assert
        assert response.status_code == 403
        assert "Invalid signature" in response.json()["detail"]

    def test_empty_payload(self, client: TestClient) -> None:
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
        response = client.post(
            "/v1/webhook",
            json=payload,
            headers={"X-Hub-Signature-256": f"sha256={signature}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["messages_received"] == 0

    def test_multiple_messages(self, client: TestClient) -> None:
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
        response = client.post(
            "/v1/webhook",
            json=payload,
            headers={"X-Hub-Signature-256": f"sha256={signature}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["messages_received"] == 2

    def test_media_message(self, client: TestClient) -> None:
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
        response = client.post(
            "/v1/webhook",
            json=payload,
            headers={"X-Hub-Signature-256": f"sha256={signature}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["messages_received"] == 1

    def test_missing_signature_header(self, client: TestClient) -> None:
        """Test that missing signature header is handled."""
        # Arrange
        payload: dict[str, list[object]] = {"entry": []}

        # Act - no signature header
        response = client.post("/v1/webhook", json=payload)

        # Assert
        assert (
            response.status_code == 422
        )  # FastAPI validation error for missing header
