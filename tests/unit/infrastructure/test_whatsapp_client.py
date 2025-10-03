"""Unit tests for WhatsApp Cloud API client."""

from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from src.infrastructure.whatsapp.client import WhatsAppClient
from src.infrastructure.whatsapp.exceptions import (
    WhatsAppAPIError,
    WhatsAppMediaError,
    WhatsAppRateLimitError,
)


class TestWhatsAppClient:
    """Test WhatsApp client."""

    @pytest.fixture
    def client(self) -> WhatsAppClient:
        """Create WhatsApp client instance."""
        return WhatsAppClient(
            phone_number_id="123456789",
            access_token="test_token",
        )

    async def test_sends_text_message(self, client: WhatsAppClient) -> None:
        """Should send text message to recipient."""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "messaging_product": "whatsapp",
            "contacts": [{"input": "+447911123456", "wa_id": "447911123456"}],
            "messages": [{"id": "wamid.test123"}],
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            # Act
            message_id = await client.send_text_message(
                to="+447911123456",
                text="Hello from Is It Stolen!",
            )

            # Assert
            assert message_id == "wamid.test123"
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args.kwargs["json"]["to"] == "+447911123456"
            assert call_args.kwargs["json"]["type"] == "text"
            assert (
                call_args.kwargs["json"]["text"]["body"] == "Hello from Is It Stolen!"
            )

    async def test_sends_template_message(self, client: WhatsAppClient) -> None:
        """Should send template message with variables."""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "messaging_product": "whatsapp",
            "contacts": [{"input": "+447911123456", "wa_id": "447911123456"}],
            "messages": [{"id": "wamid.template123"}],
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            # Act
            message_id = await client.send_template_message(
                to="+447911123456",
                template_name="item_reported",
                language_code="en",
                variables=["Bicycle", "London"],
            )

            # Assert
            assert message_id == "wamid.template123"
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args.kwargs["json"]["to"] == "+447911123456"
            assert call_args.kwargs["json"]["type"] == "template"
            assert call_args.kwargs["json"]["template"]["name"] == "item_reported"

    async def test_sends_image_message(self, client: WhatsAppClient) -> None:
        """Should send image message."""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "messaging_product": "whatsapp",
            "contacts": [{"input": "+447911123456", "wa_id": "447911123456"}],
            "messages": [{"id": "wamid.image123"}],
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            # Act
            message_id = await client.send_image(
                to="+447911123456",
                image_url="https://example.com/bike.jpg",
                caption="Stolen bike photo",
            )

            # Assert
            assert message_id == "wamid.image123"
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args.kwargs["json"]["to"] == "+447911123456"
            assert call_args.kwargs["json"]["type"] == "image"
            assert (
                call_args.kwargs["json"]["image"]["link"]
                == "https://example.com/bike.jpg"
            )
            assert call_args.kwargs["json"]["image"]["caption"] == "Stolen bike photo"

    async def test_downloads_media(self, client: WhatsAppClient) -> None:
        """Should download media from WhatsApp."""
        # Arrange
        media_id = "media123"
        media_url = "https://lookaside.fbsbx.com/whatsapp_business/attachments/"
        media_content = b"fake_image_data"

        # Mock getting media URL
        mock_url_response = Mock()
        mock_url_response.status_code = 200
        mock_url_response.json.return_value = {
            "messaging_product": "whatsapp",
            "url": media_url,
            "mime_type": "image/jpeg",
            "sha256": "test_hash",
            "file_size": len(media_content),
        }

        # Mock downloading media content
        mock_content_response = Mock()
        mock_content_response.status_code = 200
        mock_content_response.content = media_content

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = [mock_url_response, mock_content_response]

            # Act
            content = await client.download_media(media_id)

            # Assert
            assert content == media_content
            assert mock_get.call_count == 2

    async def test_retries_on_rate_limit(self, client: WhatsAppClient) -> None:
        """Should retry with exponential backoff on 429 errors."""
        # Arrange
        mock_rate_limit_response = Mock()
        mock_rate_limit_response.status_code = 429
        mock_rate_limit_response.json.return_value = {
            "error": {
                "message": "Too Many Requests",
                "type": "OAuthException",
                "code": 4,
                "error_subcode": 2494055,
                "fbtrace_id": "test123",
            }
        }

        mock_success_response = Mock()
        mock_success_response.status_code = 200
        mock_success_response.json.return_value = {
            "messaging_product": "whatsapp",
            "contacts": [{"input": "+447911123456", "wa_id": "447911123456"}],
            "messages": [{"id": "wamid.success"}],
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            # First call returns 429, second call succeeds
            mock_post.side_effect = [mock_rate_limit_response, mock_success_response]

            with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                # Act
                message_id = await client.send_text_message(
                    to="+447911123456",
                    text="Test retry",
                )

                # Assert
                assert message_id == "wamid.success"
                assert mock_post.call_count == 2
                mock_sleep.assert_called_once()  # Should have slept for backoff

    async def test_raises_error_on_api_failure(self, client: WhatsAppClient) -> None:
        """Should raise WhatsAppAPIError on API errors."""
        # Arrange
        mock_error_response = Mock()
        mock_error_response.status_code = 400
        mock_error_response.json.return_value = {
            "error": {
                "message": "Invalid phone number",
                "type": "OAuthException",
                "code": 100,
                "fbtrace_id": "test123",
            }
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_error_response

            # Act & Assert
            with pytest.raises(WhatsAppAPIError) as exc_info:
                await client.send_text_message(
                    to="invalid",
                    text="Test",
                )

            assert "Invalid phone number" in str(exc_info.value)

    async def test_raises_rate_limit_error_after_max_retries(
        self, client: WhatsAppClient
    ) -> None:
        """Should raise WhatsAppRateLimitError after max retries."""
        # Arrange
        mock_rate_limit_response = Mock()
        mock_rate_limit_response.status_code = 429
        mock_rate_limit_response.json.return_value = {
            "error": {
                "message": "Too Many Requests",
                "type": "OAuthException",
                "code": 4,
            }
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            # Always return 429
            mock_post.return_value = mock_rate_limit_response

            with patch("asyncio.sleep", new_callable=AsyncMock):
                # Act & Assert
                with pytest.raises(WhatsAppRateLimitError) as exc_info:
                    await client.send_text_message(
                        to="+447911123456",
                        text="Test",
                    )

                assert "Too Many Requests" in str(exc_info.value)
                # Should have retried max_retries times (default 3)
                assert mock_post.call_count == 4  # Initial + 3 retries

    async def test_handles_media_url_fetch_error(self, client: WhatsAppClient) -> None:
        """Should raise WhatsAppMediaError if getting media URL fails."""
        # Arrange
        mock_error_response = Mock()
        mock_error_response.status_code = 404

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_error_response

            # Act & Assert
            with pytest.raises(WhatsAppMediaError) as exc_info:
                await client.download_media("invalid_media_id")

            assert "Failed to get media URL: 404" in str(exc_info.value)

    async def test_handles_media_download_error(self, client: WhatsAppClient) -> None:
        """Should raise WhatsAppMediaError if downloading media content fails."""
        # Arrange
        mock_url_response = Mock()
        mock_url_response.status_code = 200
        mock_url_response.json.return_value = {
            "url": "https://media.example.com/file.jpg"
        }

        mock_download_response = Mock()
        mock_download_response.status_code = 500

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = [mock_url_response, mock_download_response]

            # Act & Assert
            with pytest.raises(WhatsAppMediaError) as exc_info:
                await client.download_media("media123")

            assert "Failed to download media: 500" in str(exc_info.value)

    async def test_handles_http_error_during_media_download(
        self, client: WhatsAppClient
    ) -> None:
        """Should raise WhatsAppMediaError on HTTP errors."""
        # Arrange
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.ConnectError("Connection failed")

            # Act & Assert
            with pytest.raises(WhatsAppMediaError) as exc_info:
                await client.download_media("media123")

            assert "HTTP error downloading media" in str(exc_info.value)

    async def test_handles_invalid_media_response(self, client: WhatsAppClient) -> None:
        """Should raise WhatsAppMediaError if media response is invalid."""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"invalid": "response"}  # Missing "url" key

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            # Act & Assert
            with pytest.raises(WhatsAppMediaError) as exc_info:
                await client.download_media("media123")

            assert "Invalid media response" in str(exc_info.value)
