"""Tests for WhatsApp webhook handler."""

import pytest

from src.infrastructure.whatsapp.webhook_handler import WebhookHandler

VERIFY_TOKEN = "test_verify_token"  # pragma: allowlist secret
APP_SECRET = "test_app_secret"  # pragma: allowlist secret


@pytest.fixture
def webhook_handler() -> WebhookHandler:
    """Create webhook handler for testing."""
    return WebhookHandler(verify_token=VERIFY_TOKEN, app_secret=APP_SECRET)


class TestParseButtonReply:
    """Tests for parsing button reply interactive messages."""

    @pytest.mark.asyncio
    async def test_parses_button_reply_with_id_and_title(
        self, webhook_handler: WebhookHandler
    ) -> None:
        """Test parsing button reply message with id and title."""
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "+1234567890",
                                        "id": "wamid.test123",
                                        "timestamp": "1234567890",
                                        "type": "interactive",
                                        "interactive": {
                                            "type": "button_reply",
                                            "button_reply": {
                                                "id": "button_1",
                                                "title": "Option 1",
                                            },
                                        },
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }

        messages = webhook_handler.parse_webhook_payload(payload)

        assert len(messages) == 1
        msg = messages[0]
        assert msg["from"] == "+1234567890"
        assert msg["message_id"] == "wamid.test123"
        assert msg["timestamp"] == "1234567890"
        assert msg["type"] == "interactive"
        assert msg["interactive_type"] == "button_reply"
        assert msg["button_id"] == "button_1"
        assert msg["button_title"] == "Option 1"

    @pytest.mark.asyncio
    async def test_parses_multiple_button_replies(
        self, webhook_handler: WebhookHandler
    ) -> None:
        """Test parsing multiple button reply messages in one webhook."""
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "+1234567890",
                                        "id": "wamid.msg1",
                                        "timestamp": "1234567890",
                                        "type": "interactive",
                                        "interactive": {
                                            "type": "button_reply",
                                            "button_reply": {
                                                "id": "btn_yes",
                                                "title": "Yes",
                                            },
                                        },
                                    },
                                    {
                                        "from": "+0987654321",
                                        "id": "wamid.msg2",
                                        "timestamp": "1234567891",
                                        "type": "interactive",
                                        "interactive": {
                                            "type": "button_reply",
                                            "button_reply": {
                                                "id": "btn_no",
                                                "title": "No",
                                            },
                                        },
                                    },
                                ]
                            }
                        }
                    ]
                }
            ]
        }

        messages = webhook_handler.parse_webhook_payload(payload)

        assert len(messages) == 2
        assert messages[0]["button_id"] == "btn_yes"
        assert messages[1]["button_id"] == "btn_no"

    @pytest.mark.asyncio
    async def test_maintains_backward_compatibility_with_text_messages(
        self, webhook_handler: WebhookHandler
    ) -> None:
        """Test that text message parsing still works with new interactive support."""
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "+1234567890",
                                        "id": "wamid.text123",
                                        "timestamp": "1234567890",
                                        "type": "text",
                                        "text": {"body": "Hello World"},
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }

        messages = webhook_handler.parse_webhook_payload(payload)

        assert len(messages) == 1
        msg = messages[0]
        assert msg["type"] == "text"
        assert msg["text"] == "Hello World"
        # Interactive fields should not be present
        assert "interactive_type" not in msg
        assert "button_id" not in msg


class TestParseListReply:
    """Tests for parsing list reply interactive messages."""

    @pytest.mark.asyncio
    async def test_parses_list_reply_with_full_data(
        self, webhook_handler: WebhookHandler
    ) -> None:
        """Test parsing list reply message with id, title, and description."""
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "+1234567890",
                                        "id": "wamid.list123",
                                        "timestamp": "1234567890",
                                        "type": "interactive",
                                        "interactive": {
                                            "type": "list_reply",
                                            "list_reply": {
                                                "id": "category_bicycle",
                                                "title": "Bicycle",
                                                "description": "Two-wheeled vehicle",
                                            },
                                        },
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }

        messages = webhook_handler.parse_webhook_payload(payload)

        assert len(messages) == 1
        msg = messages[0]
        assert msg["from"] == "+1234567890"
        assert msg["message_id"] == "wamid.list123"
        assert msg["type"] == "interactive"
        assert msg["interactive_type"] == "list_reply"
        assert msg["list_id"] == "category_bicycle"
        assert msg["list_title"] == "Bicycle"
        assert msg["list_description"] == "Two-wheeled vehicle"

    @pytest.mark.asyncio
    async def test_parses_list_reply_without_description(
        self, webhook_handler: WebhookHandler
    ) -> None:
        """Test parsing list reply when description field is missing."""
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "+1234567890",
                                        "id": "wamid.list123",
                                        "timestamp": "1234567890",
                                        "type": "interactive",
                                        "interactive": {
                                            "type": "list_reply",
                                            "list_reply": {
                                                "id": "opt_1",
                                                "title": "Option 1",
                                            },
                                        },
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }

        messages = webhook_handler.parse_webhook_payload(payload)

        assert len(messages) == 1
        msg = messages[0]
        assert msg["list_id"] == "opt_1"
        assert msg["list_title"] == "Option 1"
        # Description is optional, so it may or may not be present
        # Just verify it doesn't crash parsing

    @pytest.mark.asyncio
    async def test_parses_mixed_message_types(
        self, webhook_handler: WebhookHandler
    ) -> None:
        """Test parsing webhook with mix of text, button, and list messages."""
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "+1111111111",
                                        "id": "wamid.text",
                                        "timestamp": "1000000000",
                                        "type": "text",
                                        "text": {"body": "Hello"},
                                    },
                                    {
                                        "from": "+2222222222",
                                        "id": "wamid.button",
                                        "timestamp": "2000000000",
                                        "type": "interactive",
                                        "interactive": {
                                            "type": "button_reply",
                                            "button_reply": {
                                                "id": "btn_1",
                                                "title": "Button",
                                            },
                                        },
                                    },
                                    {
                                        "from": "+3333333333",
                                        "id": "wamid.list",
                                        "timestamp": "3000000000",
                                        "type": "interactive",
                                        "interactive": {
                                            "type": "list_reply",
                                            "list_reply": {
                                                "id": "list_1",
                                                "title": "List Item",
                                            },
                                        },
                                    },
                                ]
                            }
                        }
                    ]
                }
            ]
        }

        messages = webhook_handler.parse_webhook_payload(payload)

        assert len(messages) == 3
        # Text message
        assert messages[0]["type"] == "text"
        assert messages[0]["text"] == "Hello"
        # Button reply
        assert messages[1]["type"] == "interactive"
        assert messages[1]["interactive_type"] == "button_reply"
        assert messages[1]["button_id"] == "btn_1"
        # List reply
        assert messages[2]["type"] == "interactive"
        assert messages[2]["interactive_type"] == "list_reply"
        assert messages[2]["list_id"] == "list_1"


class TestInteractiveMessageValidation:
    """Tests for validation and error handling in interactive message parsing."""

    @pytest.mark.asyncio
    async def test_parses_message_when_interactive_field_missing(
        self, webhook_handler: WebhookHandler
    ) -> None:
        """Test handling when interactive field is missing from message."""
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "+1234567890",
                                        "id": "wamid.test",
                                        "timestamp": "1234567890",
                                        "type": "interactive",
                                        # Missing 'interactive' field
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }

        messages = webhook_handler.parse_webhook_payload(payload)

        # Should still parse the base message but without interactive data
        assert len(messages) == 1
        assert messages[0]["type"] == "interactive"

    @pytest.mark.asyncio
    async def test_parses_message_with_unknown_interactive_type(
        self, webhook_handler: WebhookHandler
    ) -> None:
        """Test parsing message with unknown interactive type for future compatibility."""
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "+1234567890",
                                        "id": "wamid.test",
                                        "timestamp": "1234567890",
                                        "type": "interactive",
                                        "interactive": {
                                            "type": "future_new_type",
                                            "future_new_type": {"some": "data"},
                                        },
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }

        messages = webhook_handler.parse_webhook_payload(payload)

        # Should parse without crashing
        assert len(messages) == 1
        assert messages[0]["type"] == "interactive"

    @pytest.mark.asyncio
    async def test_ignores_invalid_interactive_field_type(
        self, webhook_handler: WebhookHandler
    ) -> None:
        """Test parsing when interactive field is not a dictionary."""
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "+1234567890",
                                        "id": "wamid.test",
                                        "timestamp": "1234567890",
                                        "type": "interactive",
                                        "interactive": "invalid_string",  # Not a dict
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }

        messages = webhook_handler.parse_webhook_payload(payload)

        # Should parse base message without crashing
        assert len(messages) == 1
        assert messages[0]["type"] == "interactive"
        assert "interactive_type" not in messages[0]

    @pytest.mark.asyncio
    async def test_ignores_invalid_button_reply_type(
        self, webhook_handler: WebhookHandler
    ) -> None:
        """Test parsing when button_reply field is not a dictionary."""
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "+1234567890",
                                        "id": "wamid.test",
                                        "timestamp": "1234567890",
                                        "type": "interactive",
                                        "interactive": {
                                            "type": "button_reply",
                                            "button_reply": "invalid_string",  # Not a dict
                                        },
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }

        messages = webhook_handler.parse_webhook_payload(payload)

        assert len(messages) == 1
        assert messages[0]["interactive_type"] == "button_reply"
        assert "button_id" not in messages[0]
        assert "button_title" not in messages[0]

    @pytest.mark.asyncio
    async def test_ignores_non_string_button_id_and_title(
        self, webhook_handler: WebhookHandler
    ) -> None:
        """Test parsing when button id and title have invalid types."""
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "+1234567890",
                                        "id": "wamid.test",
                                        "timestamp": "1234567890",
                                        "type": "interactive",
                                        "interactive": {
                                            "type": "button_reply",
                                            "button_reply": {
                                                "id": 123,  # Not a string
                                                "title": None,  # Not a string
                                            },
                                        },
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }

        messages = webhook_handler.parse_webhook_payload(payload)

        assert len(messages) == 1
        assert messages[0]["interactive_type"] == "button_reply"
        # Non-string fields should be ignored
        assert "button_id" not in messages[0]
        assert "button_title" not in messages[0]

    @pytest.mark.asyncio
    async def test_ignores_invalid_list_reply_type(
        self, webhook_handler: WebhookHandler
    ) -> None:
        """Test parsing when list_reply field is not a dictionary."""
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "+1234567890",
                                        "id": "wamid.test",
                                        "timestamp": "1234567890",
                                        "type": "interactive",
                                        "interactive": {
                                            "type": "list_reply",
                                            "list_reply": "invalid_string",  # Not a dict
                                        },
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }

        messages = webhook_handler.parse_webhook_payload(payload)

        assert len(messages) == 1
        assert messages[0]["interactive_type"] == "list_reply"
        assert "list_id" not in messages[0]
        assert "list_title" not in messages[0]

    @pytest.mark.asyncio
    async def test_ignores_non_string_list_fields(
        self, webhook_handler: WebhookHandler
    ) -> None:
        """Test parsing when list id, title, and description have invalid types."""
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "+1234567890",
                                        "id": "wamid.test",
                                        "timestamp": "1234567890",
                                        "type": "interactive",
                                        "interactive": {
                                            "type": "list_reply",
                                            "list_reply": {
                                                "id": 456,  # Not a string
                                                "title": None,  # Not a string
                                                "description": [],  # Not a string
                                            },
                                        },
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }

        messages = webhook_handler.parse_webhook_payload(payload)

        assert len(messages) == 1
        assert messages[0]["interactive_type"] == "list_reply"
        # Non-string fields should be ignored
        assert "list_id" not in messages[0]
        assert "list_title" not in messages[0]
        assert "list_description" not in messages[0]
