"""Unit tests for WhatsApp webhook handler."""

import hashlib
import hmac

import pytest
from fastapi import HTTPException
from fastapi.responses import PlainTextResponse

from src.infrastructure.whatsapp.webhook_handler import (
    WebhookHandler,
    verify_webhook_signature,
)


class TestWebhookVerification:
    """Test webhook verification for initial setup."""

    def test_verifies_webhook_with_correct_token(self) -> None:
        """Should verify webhook when verify_token matches."""
        # Arrange
        handler = WebhookHandler(
            verify_token="test_verify_token",
            app_secret="test_app_secret",
        )

        # Act
        response = handler.verify_webhook(
            mode="subscribe",
            token="test_verify_token",
            challenge="challenge_string_12345",
        )

        # Assert
        assert isinstance(response, PlainTextResponse)
        assert response.body == b"challenge_string_12345"
        assert response.status_code == 200

    def test_rejects_webhook_with_incorrect_token(self) -> None:
        """Should reject webhook when verify_token doesn't match."""
        # Arrange
        handler = WebhookHandler(
            verify_token="test_verify_token",
            app_secret="test_app_secret",
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            handler.verify_webhook(
                mode="subscribe",
                token="wrong_token",
                challenge="challenge_string_12345",
            )

        assert exc_info.value.status_code == 403
        assert "Invalid verify token" in str(exc_info.value.detail)

    def test_rejects_webhook_with_incorrect_mode(self) -> None:
        """Should reject webhook when mode is not 'subscribe'."""
        # Arrange
        handler = WebhookHandler(
            verify_token="test_verify_token",
            app_secret="test_app_secret",
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            handler.verify_webhook(
                mode="unsubscribe",
                token="test_verify_token",
                challenge="challenge_string_12345",
            )

        assert exc_info.value.status_code == 403
        assert "Invalid mode" in str(exc_info.value.detail)


class TestSignatureVerification:
    """Test webhook signature verification."""

    def test_verifies_valid_signature(self) -> None:
        """Should verify valid HMAC-SHA256 signature."""
        # Arrange
        app_secret = "test_app_secret"
        payload = '{"test": "data"}'

        # Generate valid signature
        expected_signature = hmac.new(
            app_secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        signature_header = f"sha256={expected_signature}"

        # Act
        result = verify_webhook_signature(
            payload=payload,
            signature_header=signature_header,
            app_secret=app_secret,
        )

        # Assert
        assert result is True

    def test_rejects_invalid_signature(self) -> None:
        """Should reject invalid signature."""
        # Arrange
        app_secret = "test_app_secret"
        payload = '{"test": "data"}'
        signature_header = "sha256=invalid_signature_12345"

        # Act
        result = verify_webhook_signature(
            payload=payload,
            signature_header=signature_header,
            app_secret=app_secret,
        )

        # Assert
        assert result is False

    def test_rejects_signature_without_sha256_prefix(self) -> None:
        """Should reject signature without sha256= prefix."""
        # Arrange
        app_secret = "test_app_secret"
        payload = '{"test": "data"}'
        signature_header = "invalid_format"

        # Act
        result = verify_webhook_signature(
            payload=payload,
            signature_header=signature_header,
            app_secret=app_secret,
        )

        # Assert
        assert result is False


class TestWebhookPayloadParsing:
    """Test webhook payload parsing."""

    async def test_parses_text_message_webhook(self) -> None:
        """Should parse text message from webhook payload."""
        # Arrange
        handler = WebhookHandler(
            verify_token="test_verify_token",
            app_secret="test_app_secret",
        )

        payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "123456789",
                    "changes": [
                        {
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {
                                    "display_phone_number": "+447700900000",
                                    "phone_number_id": "123456789",
                                },
                                "contacts": [
                                    {
                                        "profile": {"name": "John Doe"},
                                        "wa_id": "447911123456",
                                    }
                                ],
                                "messages": [
                                    {
                                        "from": "447911123456",
                                        "id": "wamid.test123",
                                        "timestamp": "1609459200",
                                        "text": {"body": "Hello, is my bike stolen?"},
                                        "type": "text",
                                    }
                                ],
                            },
                            "field": "messages",
                        }
                    ],
                }
            ],
        }

        # Act
        messages = handler.parse_webhook_payload(payload)

        # Assert
        assert len(messages) == 1
        message = messages[0]
        assert message["from"] == "447911123456"
        assert message["message_id"] == "wamid.test123"
        assert message["type"] == "text"
        assert message["text"] == "Hello, is my bike stolen?"
        assert message["timestamp"] == "1609459200"

    async def test_parses_image_message_webhook(self) -> None:
        """Should parse image message from webhook payload."""
        # Arrange
        handler = WebhookHandler(
            verify_token="test_verify_token",
            app_secret="test_app_secret",
        )

        payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messaging_product": "whatsapp",
                                "messages": [
                                    {
                                        "from": "447911123456",
                                        "id": "wamid.image123",
                                        "timestamp": "1609459200",
                                        "type": "image",
                                        "image": {
                                            "mime_type": "image/jpeg",
                                            "sha256": "abc123hash",
                                            "id": "media_id_12345",
                                        },
                                    }
                                ],
                            }
                        }
                    ]
                }
            ],
        }

        # Act
        messages = handler.parse_webhook_payload(payload)

        # Assert
        assert len(messages) == 1
        message = messages[0]
        assert message["type"] == "image"
        assert message["media_id"] == "media_id_12345"
        assert message["mime_type"] == "image/jpeg"

    async def test_handles_empty_webhook_payload(self) -> None:
        """Should handle webhook with no messages."""
        # Arrange
        handler = WebhookHandler(
            verify_token="test_verify_token",
            app_secret="test_app_secret",
        )

        payload = {
            "object": "whatsapp_business_account",
            "entry": [],
        }

        # Act
        messages = handler.parse_webhook_payload(payload)

        # Assert
        assert messages == []

    async def test_handles_status_update_webhook(self) -> None:
        """Should handle status update webhooks gracefully."""
        # Arrange
        handler = WebhookHandler(
            verify_token="test_verify_token",
            app_secret="test_app_secret",
        )

        # Status update has "statuses" instead of "messages"
        payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messaging_product": "whatsapp",
                                "statuses": [
                                    {
                                        "id": "wamid.test123",
                                        "status": "delivered",
                                        "timestamp": "1609459200",
                                    }
                                ],
                            }
                        }
                    ]
                }
            ],
        }

        # Act
        messages = handler.parse_webhook_payload(payload)

        # Assert
        assert messages == []  # Should return empty for status updates

    async def test_handles_malformed_entry_not_list(self) -> None:
        """Should handle malformed payload where entry is not a list."""
        # Arrange
        handler = WebhookHandler(
            verify_token="test_verify_token",
            app_secret="test_app_secret",
        )

        payload = {
            "object": "whatsapp_business_account",
            "entry": "not_a_list",  # Invalid type
        }

        # Act
        messages = handler.parse_webhook_payload(payload)

        # Assert
        assert messages == []

    async def test_handles_malformed_entry_dict(self) -> None:
        """Should handle malformed entry that is not a dict."""
        # Arrange
        handler = WebhookHandler(
            verify_token="test_verify_token",
            app_secret="test_app_secret",
        )

        payload = {
            "object": "whatsapp_business_account",
            "entry": ["not_a_dict"],  # Entry item is not a dict
        }

        # Act
        messages = handler.parse_webhook_payload(payload)

        # Assert
        assert messages == []

    async def test_handles_malformed_changes_not_list(self) -> None:
        """Should handle malformed changes that is not a list."""
        # Arrange
        handler = WebhookHandler(
            verify_token="test_verify_token",
            app_secret="test_app_secret",
        )

        payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "changes": "not_a_list",  # Invalid type
                }
            ],
        }

        # Act
        messages = handler.parse_webhook_payload(payload)

        # Assert
        assert messages == []

    async def test_handles_malformed_change_dict(self) -> None:
        """Should handle malformed change that is not a dict."""
        # Arrange
        handler = WebhookHandler(
            verify_token="test_verify_token",
            app_secret="test_app_secret",
        )

        payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "changes": ["not_a_dict"],  # Change item is not a dict
                }
            ],
        }

        # Act
        messages = handler.parse_webhook_payload(payload)

        # Assert
        assert messages == []

    async def test_handles_malformed_value_not_dict(self) -> None:
        """Should handle malformed value that is not a dict."""
        # Arrange
        handler = WebhookHandler(
            verify_token="test_verify_token",
            app_secret="test_app_secret",
        )

        payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "changes": [
                        {
                            "value": "not_a_dict",  # Invalid type
                        }
                    ]
                }
            ],
        }

        # Act
        messages = handler.parse_webhook_payload(payload)

        # Assert
        assert messages == []

    async def test_handles_malformed_messages_not_list(self) -> None:
        """Should handle malformed messages that is not a list."""
        # Arrange
        handler = WebhookHandler(
            verify_token="test_verify_token",
            app_secret="test_app_secret",
        )

        payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": "not_a_list",  # Invalid type
                            }
                        }
                    ]
                }
            ],
        }

        # Act
        messages = handler.parse_webhook_payload(payload)

        # Assert
        assert messages == []

    async def test_handles_malformed_message_dict(self) -> None:
        """Should handle malformed message that is not a dict."""
        # Arrange
        handler = WebhookHandler(
            verify_token="test_verify_token",
            app_secret="test_app_secret",
        )

        payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": ["not_a_dict"],  # Message is not a dict
                            }
                        }
                    ]
                }
            ],
        }

        # Act
        messages = handler.parse_webhook_payload(payload)

        # Assert
        assert messages == []

    async def test_handles_message_with_missing_type(self) -> None:
        """Should handle message with missing type field."""
        # Arrange
        handler = WebhookHandler(
            verify_token="test_verify_token",
            app_secret="test_app_secret",
        )

        payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "447911123456",
                                        "id": "wamid.test123",
                                        "timestamp": "1609459200",
                                        # Missing "type" field
                                    }
                                ],
                            }
                        }
                    ]
                }
            ],
        }

        # Act
        messages = handler.parse_webhook_payload(payload)

        # Assert
        assert messages == []

    async def test_handles_message_with_missing_required_fields(self) -> None:
        """Should handle message with missing required fields."""
        # Arrange
        handler = WebhookHandler(
            verify_token="test_verify_token",
            app_secret="test_app_secret",
        )

        payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "type": "text",
                                        # Missing "from", "id", "timestamp"
                                    }
                                ],
                            }
                        }
                    ]
                }
            ],
        }

        # Act
        messages = handler.parse_webhook_payload(payload)

        # Assert
        assert messages == []

    async def test_handles_text_message_with_malformed_text_field(self) -> None:
        """Should handle text message with malformed text field."""
        # Arrange
        handler = WebhookHandler(
            verify_token="test_verify_token",
            app_secret="test_app_secret",
        )

        payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "447911123456",
                                        "id": "wamid.test123",
                                        "timestamp": "1609459200",
                                        "type": "text",
                                        "text": "not_a_dict",  # Should be a dict
                                    }
                                ],
                            }
                        }
                    ]
                }
            ],
        }

        # Act
        messages = handler.parse_webhook_payload(payload)

        # Assert - Should still parse message but without text content
        assert len(messages) == 1
        assert "text" not in messages[0]

    async def test_handles_text_message_with_missing_body(self) -> None:
        """Should handle text message with missing body field."""
        # Arrange
        handler = WebhookHandler(
            verify_token="test_verify_token",
            app_secret="test_app_secret",
        )

        payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "447911123456",
                                        "id": "wamid.test123",
                                        "timestamp": "1609459200",
                                        "type": "text",
                                        "text": {},  # Empty dict, no "body"
                                    }
                                ],
                            }
                        }
                    ]
                }
            ],
        }

        # Act
        messages = handler.parse_webhook_payload(payload)

        # Assert - Should parse message but without text content
        assert len(messages) == 1
        assert "text" not in messages[0]

    async def test_handles_image_message_with_malformed_image_field(self) -> None:
        """Should handle image message with malformed image field."""
        # Arrange
        handler = WebhookHandler(
            verify_token="test_verify_token",
            app_secret="test_app_secret",
        )

        payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "447911123456",
                                        "id": "wamid.image123",
                                        "timestamp": "1609459200",
                                        "type": "image",
                                        "image": "not_a_dict",  # Should be a dict
                                    }
                                ],
                            }
                        }
                    ]
                }
            ],
        }

        # Act
        messages = handler.parse_webhook_payload(payload)

        # Assert - Should parse message but without media fields
        assert len(messages) == 1
        assert "media_id" not in messages[0]
        assert "mime_type" not in messages[0]

    async def test_handles_image_message_with_missing_id(self) -> None:
        """Should handle image message with missing media ID."""
        # Arrange
        handler = WebhookHandler(
            verify_token="test_verify_token",
            app_secret="test_app_secret",
        )

        payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "447911123456",
                                        "id": "wamid.image123",
                                        "timestamp": "1609459200",
                                        "type": "image",
                                        "image": {
                                            "mime_type": "image/jpeg",
                                            # Missing "id" field
                                        },
                                    }
                                ],
                            }
                        }
                    ]
                }
            ],
        }

        # Act
        messages = handler.parse_webhook_payload(payload)

        # Assert - Should parse message with mime_type but no media_id
        assert len(messages) == 1
        assert "media_id" not in messages[0]
        assert messages[0]["mime_type"] == "image/jpeg"

    async def test_handles_video_message(self) -> None:
        """Should handle video message type."""
        # Arrange
        handler = WebhookHandler(
            verify_token="test_verify_token",
            app_secret="test_app_secret",
        )

        payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "447911123456",
                                        "id": "wamid.video123",
                                        "timestamp": "1609459200",
                                        "type": "video",
                                        "video": {
                                            "id": "video_media_id",
                                            "mime_type": "video/mp4",
                                        },
                                    }
                                ],
                            }
                        }
                    ]
                }
            ],
        }

        # Act
        messages = handler.parse_webhook_payload(payload)

        # Assert
        assert len(messages) == 1
        assert messages[0]["type"] == "video"
        assert messages[0]["media_id"] == "video_media_id"
        assert messages[0]["mime_type"] == "video/mp4"

    async def test_handles_unknown_message_type(self) -> None:
        """Should handle unknown message types gracefully."""
        # Arrange
        handler = WebhookHandler(
            verify_token="test_verify_token",
            app_secret="test_app_secret",
        )

        payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "447911123456",
                                        "id": "wamid.unknown123",
                                        "timestamp": "1609459200",
                                        "type": "unknown_type",  # Unsupported type
                                    }
                                ],
                            }
                        }
                    ]
                }
            ],
        }

        # Act
        messages = handler.parse_webhook_payload(payload)

        # Assert - Should still parse basic message info
        assert len(messages) == 1
        assert messages[0]["type"] == "unknown_type"
        assert messages[0]["from"] == "447911123456"
        # No text or media fields should be present
        assert "text" not in messages[0]
        assert "media_id" not in messages[0]

    async def test_handles_image_with_non_string_mime_type(self) -> None:
        """Should handle image with mime_type that is not a string."""
        # Arrange
        handler = WebhookHandler(
            verify_token="test_verify_token",
            app_secret="test_app_secret",
        )

        payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "447911123456",
                                        "id": "wamid.image123",
                                        "timestamp": "1609459200",
                                        "type": "image",
                                        "image": {
                                            "id": "media_id_12345",
                                            "mime_type": 123,  # Not a string
                                        },
                                    }
                                ],
                            }
                        }
                    ]
                }
            ],
        }

        # Act
        messages = handler.parse_webhook_payload(payload)

        # Assert - Should parse media_id but not mime_type
        assert len(messages) == 1
        assert messages[0]["media_id"] == "media_id_12345"
        assert "mime_type" not in messages[0]
