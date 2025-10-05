"""Metrics endpoint for tracking bot usage and performance."""

from typing import Any

from fastapi import APIRouter

from src.infrastructure.metrics.metrics_service import get_metrics_service

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("")
async def get_metrics() -> dict[str, Any]:
    """Get current metrics.

    Returns:
        Dictionary containing all current metrics
    """
    metrics_service = get_metrics_service()
    return metrics_service.get_all_metrics()


@router.post("/reset")
async def reset_metrics() -> dict[str, str]:
    """Reset all metrics to zero.

    Returns:
        Success message
    """
    metrics_service = get_metrics_service()
    metrics_service.reset_metrics()
    return {"message": "Metrics reset successfully"}
