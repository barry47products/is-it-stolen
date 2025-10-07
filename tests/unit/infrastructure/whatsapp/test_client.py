"""Tests for WhatsApp Cloud API client."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.infrastructure.whatsapp.client import WhatsAppClient
from src.infrastructure.whatsapp.exceptions import (
    WhatsAppAPIError,
    WhatsAppRateLimitError,
)

PHONE_NUMBER_ID = "1234567890"
ACCESS_TOKEN = "test_token"
RECIPIENT = "+1234567890"


@pytest.fixture
def client() -> WhatsAppClient:
    """Create WhatsApp client for testing."""
    return WhatsAppClient(
        phone_number_id=PHONE_NUMBER_ID,
        access_token=ACCESS_TOKEN,
    )


@pytest.fixture
def mock_response() -> MagicMock:
    """Create mock HTTP response."""
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"messages": [{"id": "wamid.test123"}]}
    return response


class TestSendReplyButtons:
    """Tests for send_reply_buttons method."""

    @pytest.mark.asyncio
    async def test_sends_single_button(
        self, client: WhatsAppClient, mock_response: MagicMock
    ) -> None:
        """Test sending message with single reply button."""
        buttons = [{"id": "button_1", "title": "Option 1"}]

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            message_id = await client.send_reply_buttons(
                to=RECIPIENT, body="Choose an option:", buttons=buttons
            )

            assert message_id == "wamid.test123"

            # Verify payload structure
            call_args = mock_client.return_value.__aenter__.return_value.post.call_args
            payload = call_args[1]["json"]

            assert payload["messaging_product"] == "whatsapp"
            assert payload["recipient_type"] == "individual"
            assert payload["to"] == RECIPIENT
            assert payload["type"] == "interactive"
            assert payload["interactive"]["type"] == "button"
            assert payload["interactive"]["body"]["text"] == "Choose an option:"
            assert len(payload["interactive"]["action"]["buttons"]) == 1
            assert payload["interactive"]["action"]["buttons"][0]["type"] == "reply"
            assert (
                payload["interactive"]["action"]["buttons"][0]["reply"]["id"]
                == "button_1"
            )
            assert (
                payload["interactive"]["action"]["buttons"][0]["reply"]["title"]
                == "Option 1"
            )

    @pytest.mark.asyncio
    async def test_sends_three_buttons(
        self, client: WhatsAppClient, mock_response: MagicMock
    ) -> None:
        """Test sending message with three reply buttons (maximum allowed)."""
        buttons = [
            {"id": "btn_1", "title": "Button 1"},
            {"id": "btn_2", "title": "Button 2"},
            {"id": "btn_3", "title": "Button 3"},
        ]

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            message_id = await client.send_reply_buttons(
                to=RECIPIENT, body="Pick one:", buttons=buttons
            )

            assert message_id == "wamid.test123"

            # Verify all 3 buttons in payload
            call_args = mock_client.return_value.__aenter__.return_value.post.call_args
            payload = call_args[1]["json"]
            assert len(payload["interactive"]["action"]["buttons"]) == 3

    @pytest.mark.asyncio
    async def test_raises_error_for_more_than_three_buttons(
        self, client: WhatsAppClient
    ) -> None:
        """Test that sending more than 3 buttons raises ValueError."""
        buttons = [
            {"id": f"btn_{i}", "title": f"Button {i}"}
            for i in range(4)  # 4 buttons (exceeds limit)
        ]

        with pytest.raises(ValueError, match="Maximum 3 buttons allowed"):
            await client.send_reply_buttons(
                to=RECIPIENT, body="Too many buttons", buttons=buttons
            )

    @pytest.mark.asyncio
    async def test_raises_error_for_empty_buttons(self, client: WhatsAppClient) -> None:
        """Test that sending empty buttons list raises ValueError."""
        with pytest.raises(ValueError, match="At least 1 button required"):
            await client.send_reply_buttons(to=RECIPIENT, body="No buttons", buttons=[])

    @pytest.mark.asyncio
    async def test_handles_api_error(self, client: WhatsAppClient) -> None:
        """Test handling of WhatsApp API error response."""
        error_response = MagicMock()
        error_response.status_code = 400
        error_response.json.return_value = {
            "error": {"message": "Invalid button structure", "code": 400}
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=error_response
            )

            buttons = [{"id": "btn_1", "title": "Button 1"}]

            with pytest.raises(WhatsAppAPIError, match="Invalid button structure"):
                await client.send_reply_buttons(
                    to=RECIPIENT, body="Test", buttons=buttons
                )


class TestSendListMessage:
    """Tests for send_list_message method."""

    @pytest.mark.asyncio
    async def test_sends_list_with_single_section(
        self, client: WhatsAppClient, mock_response: MagicMock
    ) -> None:
        """Test sending list message with single section."""
        sections = [
            {
                "title": "Options",
                "rows": [
                    {"id": "opt_1", "title": "Option 1", "description": "First option"},
                    {
                        "id": "opt_2",
                        "title": "Option 2",
                        "description": "Second option",
                    },
                ],
            }
        ]

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            message_id = await client.send_list_message(
                to=RECIPIENT,
                body="Choose an option:",
                button_text="View options",
                sections=sections,
            )

            assert message_id == "wamid.test123"

            # Verify payload structure
            call_args = mock_client.return_value.__aenter__.return_value.post.call_args
            payload = call_args[1]["json"]

            assert payload["messaging_product"] == "whatsapp"
            assert payload["type"] == "interactive"
            assert payload["interactive"]["type"] == "list"
            assert payload["interactive"]["body"]["text"] == "Choose an option:"
            assert payload["interactive"]["action"]["button"] == "View options"
            assert len(payload["interactive"]["action"]["sections"]) == 1
            assert payload["interactive"]["action"]["sections"][0]["title"] == "Options"
            assert len(payload["interactive"]["action"]["sections"][0]["rows"]) == 2

    @pytest.mark.asyncio
    async def test_sends_list_with_multiple_sections(
        self, client: WhatsAppClient, mock_response: MagicMock
    ) -> None:
        """Test sending list message with multiple sections."""
        sections = [
            {
                "title": "Section 1",
                "rows": [
                    {"id": "s1_opt1", "title": "S1 Option 1", "description": "Desc 1"},
                ],
            },
            {
                "title": "Section 2",
                "rows": [
                    {"id": "s2_opt1", "title": "S2 Option 1", "description": "Desc 2"},
                ],
            },
        ]

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            message_id = await client.send_list_message(
                to=RECIPIENT,
                body="Multiple sections:",
                button_text="Choose",
                sections=sections,
            )

            assert message_id == "wamid.test123"

            call_args = mock_client.return_value.__aenter__.return_value.post.call_args
            payload = call_args[1]["json"]
            assert len(payload["interactive"]["action"]["sections"]) == 2

    @pytest.mark.asyncio
    async def test_sends_list_with_optional_header(
        self, client: WhatsAppClient, mock_response: MagicMock
    ) -> None:
        """Test sending list message with optional header."""
        sections = [
            {"title": "Options", "rows": [{"id": "opt_1", "title": "Option 1"}]}
        ]

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            message_id = await client.send_list_message(
                to=RECIPIENT,
                body="Choose:",
                button_text="View",
                sections=sections,
                header="📋 Select Item",
            )

            assert message_id == "wamid.test123"

            call_args = mock_client.return_value.__aenter__.return_value.post.call_args
            payload = call_args[1]["json"]
            assert payload["interactive"]["header"]["type"] == "text"
            assert payload["interactive"]["header"]["text"] == "📋 Select Item"

    @pytest.mark.asyncio
    async def test_raises_error_for_more_than_ten_rows_total(
        self, client: WhatsAppClient
    ) -> None:
        """Test that sending more than 10 total rows raises ValueError."""
        sections = [
            {
                "title": "Section 1",
                "rows": [{"id": f"opt_{i}", "title": f"Option {i}"} for i in range(11)],
            }
        ]

        with pytest.raises(
            ValueError, match="Maximum 10 rows allowed across all sections"
        ):
            await client.send_list_message(
                to=RECIPIENT,
                body="Too many rows",
                button_text="View",
                sections=sections,
            )

    @pytest.mark.asyncio
    async def test_raises_error_for_more_than_ten_sections(
        self, client: WhatsAppClient
    ) -> None:
        """Test that sending more than 10 sections raises ValueError."""
        sections = [
            {
                "title": f"Section {i}",
                "rows": [{"id": f"opt_{i}", "title": f"Option {i}"}],
            }
            for i in range(11)  # 11 sections (exceeds limit)
        ]

        with pytest.raises(ValueError, match="Maximum 10 sections allowed"):
            await client.send_list_message(
                to=RECIPIENT,
                body="Too many sections",
                button_text="View",
                sections=sections,
            )

    @pytest.mark.asyncio
    async def test_raises_error_for_empty_sections(
        self, client: WhatsAppClient
    ) -> None:
        """Test that sending empty sections list raises ValueError."""
        with pytest.raises(ValueError, match="At least 1 section required"):
            await client.send_list_message(
                to=RECIPIENT, body="No sections", button_text="View", sections=[]
            )

    @pytest.mark.asyncio
    async def test_handles_rate_limit_error(self, client: WhatsAppClient) -> None:
        """Test handling of rate limit error."""
        error_response = MagicMock()
        error_response.status_code = 429
        error_response.json.return_value = {
            "error": {"message": "Too Many Requests", "code": 429}
        }

        with (
            patch("httpx.AsyncClient") as mock_client,
            patch("asyncio.sleep", new_callable=AsyncMock),
        ):
            # Mock all retry attempts to return 429
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=error_response
            )

            sections = [
                {"title": "Options", "rows": [{"id": "opt_1", "title": "Option 1"}]}
            ]

            with pytest.raises(WhatsAppRateLimitError, match="Too Many Requests"):
                await client.send_list_message(
                    to=RECIPIENT, body="Test", button_text="View", sections=sections
                )
