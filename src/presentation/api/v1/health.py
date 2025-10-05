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


@router.get("")
async def health_check() -> dict[str, str]:
    """Basic health check endpoint.

    Returns:
        Status message indicating service is healthy
    """
    return {"status": "healthy", "version": SERVICE_VERSION}


@router.get("/live")
async def liveness_check() -> dict[str, str]:
    """Liveness probe for Kubernetes.

    Returns:
        Status message indicating service is alive
    """
    return {"status": "alive"}


@router.get("/ready")
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
