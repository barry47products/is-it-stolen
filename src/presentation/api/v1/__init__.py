"""API v1 router configuration."""

from fastapi import APIRouter

from src.presentation.api.v1 import webhook

# Create API router for v1
api_router = APIRouter()


@api_router.get("/health")
async def health_check_v1() -> dict[str, str]:
    """Versioned health check endpoint.

    Returns:
        Status message with API version
    """
    return {"status": "healthy", "api_version": "v1"}


# Include webhook router
api_router.include_router(webhook.router)
