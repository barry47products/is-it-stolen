"""Health check endpoints for monitoring service health."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi.responses import JSONResponse

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from src.infrastructure.cache.redis_client import RedisClient
from src.infrastructure.config.settings import get_settings
from src.infrastructure.persistence.database import get_engine

router = APIRouter(prefix="/health", tags=["health"])

SERVICE_VERSION = "0.1.0"


@router.get(
    "",
    summary="Basic health check",
    description="Returns basic health status of the service without checking dependencies.",
    response_description="Service health status",
    responses={
        200: {
            "description": "Service is healthy",
            "content": {
                "application/json": {
                    "example": {"status": "healthy", "version": "0.1.0"}
                }
            },
        }
    },
)
async def health_check() -> dict[str, str]:
    """Basic health check endpoint.

    Returns:
        Status message indicating service is healthy
    """
    return {"status": "healthy", "version": SERVICE_VERSION}


@router.get(
    "/live",
    summary="Kubernetes liveness probe",
    description="""
Liveness probe endpoint for Kubernetes health checks.

Returns success if the application process is running and responsive.
Does NOT check external dependencies - use `/health/ready` for that.

Kubernetes will restart the pod if this check fails repeatedly.
    """,
    response_description="Service liveness status",
    responses={
        200: {
            "description": "Service is alive",
            "content": {"application/json": {"example": {"status": "alive"}}},
        }
    },
)
async def liveness_check() -> dict[str, str]:
    """Liveness probe for Kubernetes.

    Returns:
        Status message indicating service is alive
    """
    return {"status": "alive"}


@router.get(
    "/ready",
    summary="Kubernetes readiness probe",
    description="""
Readiness probe endpoint for Kubernetes health checks.

Verifies all critical dependencies are available:
- **PostgreSQL database** - Connection and query execution
- **Redis cache** - Connection and ping response

Returns 200 if all dependencies are healthy, 503 if any fail.
Kubernetes will remove the pod from load balancer rotation if this fails.

Use this endpoint to ensure the service is fully operational before routing traffic.
    """,
    response_description="Service readiness status with dependency health",
    responses={
        200: {
            "description": "Service is ready - all dependencies healthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "ready",
                        "database": "connected",
                        "redis": "connected",
                    }
                }
            },
        },
        503: {
            "description": "Service unavailable - one or more dependencies unhealthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "unavailable",
                        "database": "disconnected",
                        "redis": "connected",
                    }
                }
            },
        },
    },
)
async def readiness_check() -> JSONResponse:  # type: ignore[no-any-unimported]
    """Readiness probe checking all critical dependencies.

    Checks:
        - Database connectivity
        - Redis connectivity

    Returns:
        Status message with dependency health
    """
    health_status = {"status": "ready", "database": "unknown", "redis": "unknown"}
    is_healthy = True

    # Check database connectivity
    try:
        engine = get_engine()
        with engine.connect():
            health_status["database"] = "connected"
    except Exception:
        health_status["database"] = "disconnected"
        is_healthy = False

    # Check Redis connectivity
    try:
        redis_client = get_redis_client()
        redis = await redis_client._get_redis()
        await redis.ping()
        health_status["redis"] = "connected"
    except Exception:
        health_status["redis"] = "disconnected"
        is_healthy = False

    if not is_healthy:
        health_status["status"] = "unavailable"
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=health_status,
        )

    return JSONResponse(status_code=status.HTTP_200_OK, content=health_status)


def get_redis_client() -> RedisClient:
    """Get Redis client for health checks.

    Returns:
        Redis client instance
    """
    settings = get_settings()
    return RedisClient(redis_url=str(settings.redis_url))
