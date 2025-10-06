"""WhatsApp webhook endpoints (unified router).

This module re-exports the webhook verification (GET) and receiver (POST) routers
as a single unified router for backward compatibility.
"""

from fastapi import APIRouter

from src.presentation.api.v1.webhook_receiver import (
    _redact_payload_phone_numbers,
    get_client_ip,
    redact_message_data,
    redact_phone_number,
)
from src.presentation.api.v1.webhook_receiver import (
    router as receiver_router,
)
from src.presentation.api.v1.webhook_verification import router as verification_router

# Create a unified router that includes both verification and receiver
router = APIRouter(tags=["webhook"])
router.include_router(verification_router)
router.include_router(receiver_router)

# Re-export functions for backward compatibility
__all__ = [
    "_redact_payload_phone_numbers",
    "get_client_ip",
    "redact_message_data",
    "redact_phone_number",
    "router",
]
