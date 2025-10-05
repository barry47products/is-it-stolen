"""WhatsApp webhook endpoints."""

from fastapi import APIRouter, Header, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from src.infrastructure.config.settings import get_settings
from src.infrastructure.whatsapp.webhook_handler import (
    WebhookHandler,
    verify_webhook_signature,
)

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
) -> dict[str, str | int]:
    """Receive webhook events from WhatsApp.

    This endpoint handles POST requests containing message events from WhatsApp.
    It verifies the signature, parses messages, and queues them for processing.

    Args:
        request: FastAPI request containing the webhook payload
        x_hub_signature_256: HMAC SHA256 signature header for verification

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

    # TODO: Queue messages for processing
    # For now, just acknowledge receipt
    # In Issue #33 we'll implement the conversation state machine

    return {"status": "success", "messages_received": len(messages)}
