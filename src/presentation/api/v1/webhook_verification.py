"""WhatsApp webhook verification endpoint."""

import logging

from fastapi import APIRouter, Query
from fastapi.responses import PlainTextResponse

from src.infrastructure.config.settings import get_settings
from src.infrastructure.whatsapp.webhook_handler import WebhookHandler

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


@router.get(
    "/webhook",
    summary="Verify WhatsApp webhook subscription",
    description="""
Verifies webhook subscription during initial setup in Meta Developer Portal.

When configuring the webhook URL in the WhatsApp Business API settings,
Meta sends a GET request to verify ownership of the endpoint.

## Verification Flow

1. Meta sends GET request with query parameters
2. Endpoint validates `hub.verify_token` matches configured token
3. If valid, returns `hub.challenge` as plain text
4. Meta confirms subscription is active

## Usage

This endpoint is called automatically by Meta - you don't invoke it directly.
Configure your webhook in the Meta Developer Portal with:
- **Webhook URL**: `https://your-domain.com/v1/webhook`
- **Verify Token**: Your configured `WHATSAPP_WEBHOOK_VERIFY_TOKEN`

Meta will call this endpoint to verify and activate the subscription.
    """,
    response_class=PlainTextResponse,
    response_description="Challenge string echoed back for verification",
    responses={
        200: {
            "description": "Verification successful - challenge echoed",
            "content": {"text/plain": {"example": "1234567890"}},
        },
        403: {
            "description": "Verification failed - invalid token",
            "content": {
                "application/json": {
                    "example": {"detail": "Webhook verification failed"}
                }
            },
        },
    },
)
async def verify_webhook(  # type: ignore[no-any-unimported]
    hub_mode: str = Query(
        alias="hub.mode", description="Subscription mode (should be 'subscribe')"
    ),
    hub_verify_token: str = Query(
        alias="hub.verify_token",
        description="Verification token to validate against configured token",
    ),
    hub_challenge: str = Query(
        alias="hub.challenge", description="Challenge string to echo back if valid"
    ),
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
