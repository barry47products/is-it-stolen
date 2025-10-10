"""Metrics endpoint for tracking bot usage and performance."""

from typing import Any

from fastapi import APIRouter

from src.infrastructure.metrics.metrics_service import get_metrics_service

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get(
    "",
    summary="Get application metrics",
    description="""
Retrieves current application metrics for monitoring and observability.

Provides real-time statistics including:
- **Message counts** - Total messages processed
- **User activity** - Active users and sessions
- **Conversation states** - Distribution across states
- **Performance** - Response times and error rates

These metrics complement Prometheus metrics exposed at `/metrics` (root level).
    """,
    response_description="Current application metrics",
    responses={
        200: {
            "description": "Metrics retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "messages_processed": 1234,
                        "active_users": 56,
                        "avg_response_time_ms": 245,
                        "error_rate": 0.02,
                    }
                }
            },
        }
    },
)
async def get_metrics() -> dict[str, Any]:
    """Get current metrics.

    Returns:
        Dictionary containing all current metrics
    """
    metrics_service = get_metrics_service()
    return metrics_service.get_all_metrics()


@router.post(
    "/reset",
    summary="Reset application metrics",
    description="""
Resets all application metrics to zero.

**Warning**: This operation is destructive and cannot be undone.
Should only be used in development/testing environments.

Does NOT affect Prometheus metrics - those are managed separately.
    """,
    response_description="Metrics reset confirmation",
    responses={
        200: {
            "description": "Metrics reset successfully",
            "content": {
                "application/json": {
                    "example": {"message": "Metrics reset successfully"}
                }
            },
        }
    },
)
async def reset_metrics() -> dict[str, str]:
    """Reset all metrics to zero.

    Returns:
        Success message
    """
    metrics_service = get_metrics_service()
    metrics_service.reset_metrics()
    return {"message": "Metrics reset successfully"}
