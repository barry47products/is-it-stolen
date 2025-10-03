"""WhatsApp Cloud API client."""

import asyncio
from typing import Any

import httpx

from src.infrastructure.whatsapp.exceptions import (
    WhatsAppAPIError,
    WhatsAppMediaError,
    WhatsAppRateLimitError,
)

WHATSAPP_API_VERSION = "v21.0"
WHATSAPP_BASE_URL = "https://graph.facebook.com"
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 1.0
BACKOFF_MULTIPLIER = 2.0


class WhatsAppClient:
    """WhatsApp Cloud API client with retry logic.

    Provides methods to send messages, templates, media, and download
    media from WhatsApp Business Cloud API.
    """

    def __init__(
        self,
        phone_number_id: str,
        access_token: str,
        max_retries: int = DEFAULT_MAX_RETRIES,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        """Initialize WhatsApp client.

        Args:
            phone_number_id: WhatsApp Business phone number ID
            access_token: WhatsApp Business API access token
            max_retries: Maximum number of retries for rate limits
            timeout: Request timeout in seconds
        """
        self.phone_number_id = phone_number_id
        self.access_token = access_token
        self.max_retries = max_retries
        self.timeout = timeout
        self.base_url = f"{WHATSAPP_BASE_URL}/{WHATSAPP_API_VERSION}"

    async def send_text_message(self, to: str, text: str) -> str:
        """Send text message to recipient.

        Args:
            to: Recipient phone number in E.164 format
            text: Message text

        Returns:
            Message ID from WhatsApp

        Raises:
            WhatsAppAPIError: If API returns an error
            WhatsAppRateLimitError: If rate limit exceeded after retries
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"body": text},
        }

        response = await self._send_message(payload)
        return str(response["messages"][0]["id"])

    async def send_template_message(
        self,
        to: str,
        template_name: str,
        language_code: str,
        variables: list[str] | None = None,
    ) -> str:
        """Send template message with variables.

        Args:
            to: Recipient phone number in E.164 format
            template_name: Name of approved template
            language_code: Language code (e.g., "en", "en_US")
            variables: List of variable values for template

        Returns:
            Message ID from WhatsApp

        Raises:
            WhatsAppAPIError: If API returns an error
            WhatsAppRateLimitError: If rate limit exceeded after retries
        """
        components = []
        if variables:
            parameters = [{"type": "text", "text": var} for var in variables]
            components.append({"type": "body", "parameters": parameters})

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code},
                "components": components,
            },
        }

        response = await self._send_message(payload)
        return str(response["messages"][0]["id"])

    async def send_image(
        self, to: str, image_url: str, caption: str | None = None
    ) -> str:
        """Send image message.

        Args:
            to: Recipient phone number in E.164 format
            image_url: URL of image to send
            caption: Optional image caption

        Returns:
            Message ID from WhatsApp

        Raises:
            WhatsAppAPIError: If API returns an error
            WhatsAppRateLimitError: If rate limit exceeded after retries
        """
        image_data: dict[str, Any] = {"link": image_url}
        if caption:
            image_data["caption"] = caption

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "image",
            "image": image_data,
        }

        response = await self._send_message(payload)
        return str(response["messages"][0]["id"])

    async def download_media(self, media_id: str) -> bytes:
        """Download media from WhatsApp.

        Args:
            media_id: Media ID from WhatsApp message

        Returns:
            Media content as bytes

        Raises:
            WhatsAppMediaError: If media download fails
        """
        try:
            # Step 1: Get media URL
            url = f"{self.base_url}/{media_id}"
            headers = {"Authorization": f"Bearer {self.access_token}"}

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers)

                if response.status_code != 200:
                    raise WhatsAppMediaError(
                        f"Failed to get media URL: {response.status_code}"
                    )

                media_info = response.json()
                media_url = media_info["url"]

                # Step 2: Download media content
                media_response = await client.get(media_url, headers=headers)

                if media_response.status_code != 200:
                    raise WhatsAppMediaError(
                        f"Failed to download media: {media_response.status_code}"
                    )

                content: bytes = media_response.content
                return content

        except httpx.HTTPError as e:
            raise WhatsAppMediaError(f"HTTP error downloading media: {e}") from e
        except KeyError as e:
            raise WhatsAppMediaError(f"Invalid media response: {e}") from e

    async def _send_message(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Send message with retry logic.

        Args:
            payload: Message payload

        Returns:
            API response JSON

        Raises:
            WhatsAppAPIError: If API returns an error
            WhatsAppRateLimitError: If rate limit exceeded after retries
        """
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        last_error: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(url, headers=headers, json=payload)

                    # Handle rate limiting with exponential backoff
                    if response.status_code == 429:
                        if attempt < self.max_retries:
                            backoff = INITIAL_BACKOFF_SECONDS * (
                                BACKOFF_MULTIPLIER**attempt
                            )
                            await asyncio.sleep(backoff)
                            continue

                        # Max retries exceeded
                        error_data = response.json().get("error", {})
                        raise WhatsAppRateLimitError(
                            error_data.get("message", "Too Many Requests")
                        )

                    # Handle other errors
                    if response.status_code != 200:
                        error_data = response.json().get("error", {})
                        raise WhatsAppAPIError(
                            message=error_data.get("message", "Unknown error"),
                            error_code=error_data.get("code"),
                        )

                    result: dict[str, Any] = response.json()
                    return result

            except (httpx.HTTPError, WhatsAppAPIError, WhatsAppRateLimitError) as e:
                last_error = e
                if isinstance(e, WhatsAppRateLimitError) and attempt < self.max_retries:
                    backoff = INITIAL_BACKOFF_SECONDS * (BACKOFF_MULTIPLIER**attempt)
                    await asyncio.sleep(backoff)
                    continue
                raise

        # Should never reach here, but just in case
        if last_error:
            raise last_error
        raise WhatsAppAPIError("Unknown error occurred")
