"""API v1 router configuration."""

from fastapi import APIRouter

from src.presentation.api.v1 import health, webhook

# Create API router for v1
api_router = APIRouter()

# Include health check router
api_router.include_router(health.router)

# Include webhook router
api_router.include_router(webhook.router)
