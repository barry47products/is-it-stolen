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
    latitude: str
    longitude: str
    location_name: str
    location_address: str


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

    def verify_webhook(  # type: ignore[no-any-unimported]
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
            entry_messages = self._extract_messages_from_entry(entry)
            messages.extend(entry_messages)

        return messages

    def _extract_messages_from_entry(self, entry: object) -> list[dict[str, str]]:
        """Extract messages from a webhook entry.

        Args:
            entry: Entry object from webhook payload

        Returns:
            List of parsed messages from this entry
        """
        if not isinstance(entry, dict):
            return []

        changes = entry.get("changes", [])
        if not isinstance(changes, list):
            return []

        messages: list[dict[str, str]] = []
        for change in changes:
            change_messages = self._extract_messages_from_change(change)
            messages.extend(change_messages)

        return messages

    def _extract_messages_from_change(self, change: object) -> list[dict[str, str]]:
        """Extract messages from a webhook change.

        Args:
            change: Change object from webhook entry

        Returns:
            List of parsed messages from this change
        """
        if not isinstance(change, dict):
            return []

        value = change.get("value", {})
        if not isinstance(value, dict):
            return []

        webhook_messages = value.get("messages", [])
        if not isinstance(webhook_messages, list):
            return []

        return self._parse_messages_list(webhook_messages)

    def _parse_messages_list(
        self, webhook_messages: list[object]
    ) -> list[dict[str, str]]:
        """Parse a list of webhook messages.

        Args:
            webhook_messages: List of message objects

        Returns:
            List of successfully parsed messages
        """
        messages: list[dict[str, str]] = []

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
        base_fields = self._extract_base_fields(msg)
        if not base_fields:
            return None

        msg_type = base_fields["type"]
        self._add_message_content(msg, msg_type, base_fields)

        return base_fields

    def _extract_base_fields(self, msg: dict[str, object]) -> dict[str, str] | None:
        """Extract base fields from message.

        Args:
            msg: Message dictionary

        Returns:
            Dict with base fields or None if validation fails
        """
        msg_type = msg.get("type")
        if not isinstance(msg_type, str):
            return None

        from_number = msg.get("from")
        message_id = msg.get("id")
        timestamp = msg.get("timestamp")

        if not all(isinstance(x, str) for x in [from_number, message_id, timestamp]):
            return None

        return {
            "from": str(from_number),
            "message_id": str(message_id),
            "timestamp": str(timestamp),
            "type": msg_type,
        }

    def _add_message_content(
        self, msg: dict[str, object], msg_type: str, parsed: dict[str, str]
    ) -> None:
        """Add message content to parsed dict based on message type.

        Args:
            msg: Message dictionary
            msg_type: Type of message
            parsed: Parsed message dict to update
        """
        if msg_type == "text":
            self._add_text_content(msg, parsed)
        elif msg_type in ("image", "video", "document", "audio"):
            self._add_media_content(msg, msg_type, parsed)
        elif msg_type == "location":
            self._add_location_content(msg, parsed)
        elif msg_type == "interactive":
            self._add_interactive_content(msg, parsed)

    def _add_text_content(self, msg: dict[str, object], parsed: dict[str, str]) -> None:
        """Add text content to parsed message.

        Args:
            msg: Message dictionary
            parsed: Parsed message dict to update
        """
        text_data = msg.get("text", {})
        if not isinstance(text_data, dict):
            return

        body = text_data.get("body")
        if isinstance(body, str):
            parsed["text"] = body

    def _add_media_content(
        self, msg: dict[str, object], msg_type: str, parsed: dict[str, str]
    ) -> None:
        """Add media content to parsed message.

        Args:
            msg: Message dictionary
            msg_type: Media type (image, video, document, audio)
            parsed: Parsed message dict to update
        """
        media_data = msg.get(msg_type, {})
        if not isinstance(media_data, dict):
            return

        media_id = media_data.get("id")
        if isinstance(media_id, str):
            parsed["media_id"] = media_id

        mime_type = media_data.get("mime_type")
        if isinstance(mime_type, str):
            parsed["mime_type"] = mime_type

    def _add_location_content(
        self, msg: dict[str, object], parsed: dict[str, str]
    ) -> None:
        """Add location content to parsed message.

        Args:
            msg: Message dictionary
            parsed: Parsed message dict to update
        """
        location_data = msg.get("location", {})
        if not isinstance(location_data, dict):
            return

        latitude = location_data.get("latitude")
        longitude = location_data.get("longitude")

        if isinstance(latitude, (int, float)):
            parsed["latitude"] = str(latitude)

        if isinstance(longitude, (int, float)):
            parsed["longitude"] = str(longitude)

        # Optional fields
        location_name = location_data.get("name")
        if isinstance(location_name, str):
            parsed["location_name"] = location_name

        location_address = location_data.get("address")
        if isinstance(location_address, str):
            parsed["location_address"] = location_address

    def _add_interactive_content(
        self, msg: dict[str, object], parsed: dict[str, str]
    ) -> None:
        """Add interactive message content to parsed message.

        Args:
            msg: Message dictionary
            parsed: Parsed message dict to update
        """
        interactive_data = msg.get("interactive", {})
        if not isinstance(interactive_data, dict):
            return

        interactive_type = interactive_data.get("type")
        if not isinstance(interactive_type, str):
            return

        parsed["interactive_type"] = interactive_type

        if interactive_type == "button_reply":
            self._add_button_reply_content(interactive_data, parsed)
        elif interactive_type == "list_reply":
            self._add_list_reply_content(interactive_data, parsed)

    def _add_button_reply_content(
        self, interactive_data: dict[str, object], parsed: dict[str, str]
    ) -> None:
        """Add button reply content to parsed message.

        Args:
            interactive_data: Interactive data dictionary
            parsed: Parsed message dict to update
        """
        button_reply = interactive_data.get("button_reply", {})
        if not isinstance(button_reply, dict):
            return

        button_id = button_reply.get("id")
        if isinstance(button_id, str):
            parsed["button_id"] = button_id

        button_title = button_reply.get("title")
        if isinstance(button_title, str):
            parsed["button_title"] = button_title

    def _add_list_reply_content(
        self, interactive_data: dict[str, object], parsed: dict[str, str]
    ) -> None:
        """Add list reply content to parsed message.

        Args:
            interactive_data: Interactive data dictionary
            parsed: Parsed message dict to update
        """
        list_reply = interactive_data.get("list_reply", {})
        if not isinstance(list_reply, dict):
            return

        list_id = list_reply.get("id")
        if isinstance(list_id, str):
            parsed["list_id"] = list_id

        list_title = list_reply.get("title")
        if isinstance(list_title, str):
            parsed["list_title"] = list_title

        # Description is optional
        list_description = list_reply.get("description")
        if isinstance(list_description, str):
            parsed["list_description"] = list_description
