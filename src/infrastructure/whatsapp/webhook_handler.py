"""WhatsApp webhook handler with signature verification."""

import hashlib
import hmac
from collections.abc import Mapping
from typing import TypedDict

from fastapi import HTTPException
from fastapi.responses import PlainTextResponse


class ParsedMessage(TypedDict, total=False):
    """Parsed message from webhook."""

    from_: str
    message_id: str
    timestamp: str
    type: str
    text: str
    media_id: str
    mime_type: str


def verify_webhook_signature(
    payload: str,
    signature_header: str,
    app_secret: str,
) -> bool:
    """Verify webhook signature using HMAC-SHA256.

    Args:
        payload: Raw webhook payload as string
        signature_header: X-Hub-Signature-256 header value
        app_secret: WhatsApp app secret for signature verification

    Returns:
        True if signature is valid, False otherwise
    """
    if not signature_header.startswith("sha256="):
        return False

    # Extract signature from header (remove 'sha256=' prefix)
    received_signature = signature_header.removeprefix("sha256=")

    # Generate expected signature
    expected_signature = hmac.new(
        app_secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    # Use timing-safe comparison to prevent timing attacks
    return hmac.compare_digest(received_signature, expected_signature)


class WebhookHandler:
    """Handler for WhatsApp Cloud API webhooks."""

    def __init__(self, verify_token: str, app_secret: str) -> None:
        """Initialize webhook handler.

        Args:
            verify_token: Token for webhook verification during setup
            app_secret: App secret for signature verification
        """
        self.verify_token = verify_token
        self.app_secret = app_secret

    async def verify_webhook(  # type: ignore[no-any-unimported]
        self,
        mode: str,
        token: str,
        challenge: str,
    ) -> PlainTextResponse:
        """Verify webhook during initial setup.

        This handles GET requests from WhatsApp to verify the webhook endpoint.

        Args:
            mode: Verification mode (should be 'subscribe')
            token: Verification token to validate
            challenge: Challenge string to echo back

        Returns:
            PlainTextResponse with challenge string

        Raises:
            HTTPException: If verification fails
        """
        if mode != "subscribe":
            raise HTTPException(status_code=403, detail="Invalid mode")

        if token != self.verify_token:
            raise HTTPException(status_code=403, detail="Invalid verify token")

        return PlainTextResponse(content=challenge, status_code=200)

    def parse_webhook_payload(
        self,
        payload: Mapping[str, object],
    ) -> list[dict[str, str]]:
        """Parse webhook payload to extract messages.

        Args:
            payload: Webhook payload dictionary

        Returns:
            List of parsed messages
        """
        messages: list[dict[str, str]] = []

        entries = payload.get("entry", [])
        if not isinstance(entries, list):
            return messages

        for entry in entries:
            if not isinstance(entry, dict):
                continue

            changes = entry.get("changes", [])
            if not isinstance(changes, list):
                continue

            for change in changes:
                if not isinstance(change, dict):
                    continue

                value = change.get("value", {})
                if not isinstance(value, dict):
                    continue

                # Extract messages (skip if this is a status update)
                webhook_messages = value.get("messages", [])
                if not isinstance(webhook_messages, list):
                    continue

                for msg in webhook_messages:
                    if not isinstance(msg, dict):
                        continue

                    parsed = self._parse_message(msg)
                    if parsed:
                        messages.append(parsed)

        return messages

    def _parse_message(self, msg: dict[str, object]) -> dict[str, str] | None:
        """Parse individual message from webhook.

        Args:
            msg: Message dictionary from webhook

        Returns:
            Parsed message dict or None if parsing fails
        """
        msg_type = msg.get("type")
        if not isinstance(msg_type, str):
            return None

        from_number = msg.get("from")
        message_id = msg.get("id")
        timestamp = msg.get("timestamp")

        if not all(isinstance(x, str) for x in [from_number, message_id, timestamp]):
            return None

        parsed: dict[str, str] = {
            "from": str(from_number),
            "message_id": str(message_id),
            "timestamp": str(timestamp),
            "type": msg_type,
        }

        # Parse message content based on type
        if msg_type == "text":
            text_data = msg.get("text", {})
            if isinstance(text_data, dict):
                body = text_data.get("body")
                if isinstance(body, str):
                    parsed["text"] = body

        elif msg_type in ("image", "video", "document", "audio"):
            media_data = msg.get(msg_type, {})
            if isinstance(media_data, dict):
                media_id = media_data.get("id")
                mime_type = media_data.get("mime_type")
                if isinstance(media_id, str):
                    parsed["media_id"] = media_id
                if isinstance(mime_type, str):
                    parsed["mime_type"] = mime_type

        return parsed
