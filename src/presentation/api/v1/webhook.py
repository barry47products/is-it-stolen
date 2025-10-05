"""WhatsApp webhook endpoints."""

import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from src.infrastructure.config.settings import get_settings
from src.infrastructure.whatsapp.webhook_handler import (
    WebhookHandler,
    verify_webhook_signature,
)
from src.presentation.api.dependencies import get_message_processor
from src.presentation.bot.message_processor import MessageProcessor

logger = logging.getLogger(__name__)

router = APIRouter(tags=["webhook"])


def get_webhook_handler() -> WebhookHandler:
    """Get webhook handler with settings.

    Returns:
        Configured webhook handler instance
    """
    settings = get_settings()
    return WebhookHandler(
        verify_token=settings.whatsapp_webhook_verify_token,
        app_secret=settings.whatsapp_app_secret,
    )


@router.get("/webhook")
async def verify_webhook(  # type: ignore[no-any-unimported]
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge"),
) -> PlainTextResponse:
    """Verify webhook endpoint for WhatsApp.

    This endpoint handles GET requests from WhatsApp to verify the webhook
    during initial setup.

    Args:
        hub_mode: Mode parameter (should be 'subscribe')
        hub_verify_token: Verification token to validate
        hub_challenge: Challenge string to echo back

    Returns:
        PlainTextResponse with challenge string if verification succeeds

    Raises:
        HTTPException: If verification fails (403)
    """
    handler = get_webhook_handler()
    return handler.verify_webhook(
        mode=hub_mode,
        token=hub_verify_token,
        challenge=hub_challenge,
    )


@router.post("/webhook", status_code=200)
async def receive_webhook(  # type: ignore[no-any-unimported]
    request: Request,
    x_hub_signature_256: str = Header(alias="X-Hub-Signature-256"),
    message_processor: MessageProcessor = Depends(get_message_processor),
) -> dict[str, str | int]:
    """Receive webhook events from WhatsApp.

    This endpoint handles POST requests containing message events from WhatsApp.
    It verifies the signature, parses messages, and processes them through
    the conversation state machine.

    Args:
        request: FastAPI request containing the webhook payload
        x_hub_signature_256: HMAC SHA256 signature header for verification
        message_processor: Message processor for handling conversations

    Returns:
        Success response dict

    Raises:
        HTTPException: If signature verification fails (403)
    """
    settings = get_settings()

    # Read raw body for signature verification
    body = await request.body()
    payload_str = body.decode("utf-8")

    # Verify signature
    if not verify_webhook_signature(
        payload=payload_str,
        signature_header=x_hub_signature_256,
        app_secret=settings.whatsapp_app_secret,
    ):
        raise HTTPException(status_code=403, detail="Invalid signature")

    # Parse JSON payload
    payload = await request.json()

    # Parse messages from webhook
    handler = get_webhook_handler()
    messages = handler.parse_webhook_payload(payload)

    # Process each message through state machine
    # Messages will be processed asynchronously
    # In Issue #34 we'll implement the full message routing logic
    processed_count = 0
    failed_count = 0

    for msg in messages:
        phone_number = msg.get("from", "")
        message_text = msg.get("text", "")

        if not phone_number or not message_text:
            logger.warning(
                "Skipping message with missing phone_number or text",
                extra={"webhook_message": msg},
            )
            failed_count += 1
            continue

        try:
            # Process message through state machine
            response = await message_processor.process_message(
                phone_number, message_text
            )
            logger.info(
                "Message processed successfully",
                extra={
                    "phone_number": phone_number,
                    "state": response.get("state"),
                },
            )
            processed_count += 1

            # TODO: Send response back to user via WhatsApp API (Issue #34)

        except Exception as e:
            logger.error(
                "Failed to process message",
                extra={"phone_number": phone_number, "error": str(e)},
                exc_info=True,
            )
            failed_count += 1
            # Continue processing other messages even if one fails

    return {
        "status": "success",
        "messages_received": len(messages),
        "processed": processed_count,
        "failed": failed_count,
    }
